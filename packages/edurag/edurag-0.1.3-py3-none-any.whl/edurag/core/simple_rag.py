"""Simple RAG implementation

Simple RAG based on ConversationalRetrievalChain,
multiple conversations and customizable teacher personas are supported.
"""

from pathlib import Path
from typing import Optional, Union

from langchain_core.documents import Document
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_core.prompts import SystemMessagePromptTemplate, ChatPromptTemplate
from langchain_core.messages import SystemMessage

from edurag.config import EduRAGConfig
from edurag.prompt.teacher_profile import TeacherProfile
from edurag.llm.provider import create_llm, create_embeddings
from edurag.document.loader import DocumentLoader
from edurag.document.splitter import create_splitter
from edurag.vectorstore.faiss_store import FAISSVectorStore


class SimpleRAG:
    """Simple RAG Implementation
    
    A retrieval-augmented generation (RAG) question-answering system that supports:
    - Multiple LLMs (OpenAI, Gemini, Ollama)
    - Multiple document formats (PDF, DOCX, TXT)
    - Custom teacher personas
    - Multi-turn conversation history
    
    Example:
        >>> from edurag import SimpleRAG, TeacherProfile
        >>> 
        >>> teacher = TeacherProfile(
        ...     name="Dr. Lee",
        ...     subject="AP Physics",
        ...     grade_level="Grade 10-12",
        ...     teaching_style="Detailed and patient, good at explaining physics concepts by examples from daily life."
        ... )
        >>> 
        >>> rag = SimpleRAG(
        ...     api_key="sk-xxx",
        ...     teacher_profile=teacher
        ... )
        >>> rag.load_documents(["AP Physics Textbook.pdf"])
        >>> 
        >>> answer = rag.ask("What is Newton’s Second Law of Motion？")
        >>> print(answer)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4o",
        teacher_profile: Optional[TeacherProfile] = None,
        config: Optional[EduRAGConfig] = None,
        **kwargs
    ):
        """Initialize SimpleRAG
        
        Args:
            api_key: LLM API key
            llm_provider: LLM provider (openai/gemini/ollama)
            llm_model: Model name
            teacher_profile: Teacher persona configuration
            config: Full configuration object (takes priority over individual parameters)
            **kwargs: Additional configuration parameters, passed to EduRAGConfig
        """
        # Config handling
        if config is not None:
            self.config = config
        else:
            config_kwargs = {
                "llm_provider": llm_provider,
                "llm_model": llm_model,
                **kwargs
            }
            if api_key:
                config_kwargs["api_key"] = api_key
            self.config = EduRAGConfig(**config_kwargs)
        
        self.teacher_profile = teacher_profile
        self.chat_history: list[tuple[str, str]] = []
        
        # Initialize LLM
        self._llm = create_llm(
            provider=self.config.llm_provider,
            model=self.config.llm_model,
            api_key=self.config.api_key,
            api_base=self.config.api_base,
            temperature=self.config.temperature
        )
        
        # Initialize Embeddings
        self._embeddings = create_embeddings(
            provider=self.config.llm_provider,
            model=self.config.embedding_model if self.config.llm_provider == "openai" else None,
            api_key=self.config.api_key,
            api_base=self.config.api_base
        )
        
        # Vector store (lazy initialization)
        self._vectorstore: Optional[FAISSVectorStore] = None
        self._qa_chain = None
        
        # If a persistence path is configured and exists, attempt to load it.
        if self.config.vectorstore_path:
            path = Path(self.config.vectorstore_path)
            if path.exists():
                self._load_vectorstore(path)
    
    def load_documents(
        self,
        sources: Union[str, Path, list[Union[str, Path]]],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> int:
        """Load documents into the knowledge base
        
        Args:
            sources: Document paths, which can be:
                - A single file path
                - A directory path (automatically loads all supported files in the directory)
                - A list of file paths
            chunk_size: Chunk size for document splitting; uses the default configuration if None
            chunk_overlap: Overlap size between chunks; uses the default configuration if None
            
        Returns:
            Number of loaded document chunks
        """
        # Standardize input
        if isinstance(sources, (str, Path)):
            sources = [sources]
        
        # Load documents
        all_docs = []
        for source in sources:
            path = Path(source)
            if path.is_dir():
                docs = DocumentLoader.load_directory(path)
            else:
                docs = DocumentLoader.load(path)
            all_docs.extend(docs)
        
        if not all_docs:
            raise ValueError("No document loaded.")
        
        # Split documents
        splitter = create_splitter(
            method="recursive",
            chunk_size=chunk_size or self.config.chunk_size,
            chunk_overlap=chunk_overlap or self.config.chunk_overlap
        )
        split_docs = splitter.split_documents(all_docs)
        
        # Build vectorstore
        if self._vectorstore is None:
            self._vectorstore = FAISSVectorStore(self._embeddings)
        
        self._vectorstore.add_documents(split_docs)
        
        # Rebuild QA chains
        self._build_qa_chain()
        
        # Enable persistence if a path is configured
        if self.config.vectorstore_path:
            self._vectorstore.save(self.config.vectorstore_path)
        
        return len(split_docs)
    
    def add_documents(self, documents: list[Document]) -> int:
        """Add Document objects directly
        
        Args:
            documents: LangChain Document list
            
        Returns:
            Number of documents added
        """
        if self._vectorstore is None:
            self._vectorstore = FAISSVectorStore(self._embeddings)
        
        self._vectorstore.add_documents(documents)
        self._build_qa_chain()
        
        return len(documents)
    
    def _load_vectorstore(self, path: Path) -> None:
        """Load existing vectorstore"""
        self._vectorstore = FAISSVectorStore.from_local(path, self._embeddings)
        self._build_qa_chain()
    
    def _build_qa_chain(self) -> None:
        """Build QA chain"""
        if self._vectorstore is None:
            return
        
        retriever = self._vectorstore.as_retriever(
            top_k=self.config.retrieval_top_k
        )
        
        self._qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self._llm,
            retriever=retriever,
            return_source_documents=True,
            verbose=False
        )
    
    def ask(
        self,
        question: str,
        use_teacher_prompt: bool = True
    ) -> str:
        """Ask a question and get an answer
        
        Args:
            question: User question
            use_teacher_prompt: Whether to rewrite the question using the teacher persona

        Returns:
            AI generated response
        """
        if self._qa_chain is None:
            raise RuntimeError(
                "The knowledge base has not been initialized. Please call load_documents() to load the documents first."
            )
        
        # Build the query
        if use_teacher_prompt and self.teacher_profile:
            query = self.teacher_profile.to_rewrite_prompt(question)
        else:
            query = question
        
        # Execute the query
        result = self._qa_chain.invoke({
            "question": query,
            "chat_history": self.chat_history
        })
        
        answer = result["answer"]
        
        # Update chat history
        self.chat_history.append((question, answer))
        
        return answer
    
    def ask_with_sources(
        self,
        question: str,
        use_teacher_prompt: bool = True
    ) -> dict:
        """Ask a question and return the answer along with the source documents
        
        Args:
            question: User question
            use_teacher_prompt: Use teacher persona for question rewriting
            
        Returns:
            A dictionary containing `answer` and `source_documents`
        """
        if self._qa_chain is None:
            raise RuntimeError(
                "The knowledge base has not been initialized. Please call load_documents() to load the documents first."
            )
        
        if use_teacher_prompt and self.teacher_profile:
            query = self.teacher_profile.to_rewrite_prompt(question)
        else:
            query = question
        
        result = self._qa_chain.invoke({
            "question": query,
            "chat_history": self.chat_history
        })
        
        answer = result["answer"]
        self.chat_history.append((question, answer))
        
        return {
            "answer": answer,
            "source_documents": result.get("source_documents", [])
        }
    
    def search(self, query: str, top_k: int = 4) -> list[Document]:
        """Directly search for relevant documents (without generating an answer)
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of relevant documents
        """
        if self._vectorstore is None:
            raise RuntimeError("The knowledge base has not been initialized.")
        
        return self._vectorstore.search(query, top_k=top_k)
    
    def clear_history(self) -> None:
        """Clear chat history"""
        self.chat_history = []
    
    def save_vectorstore(self, path: Union[str, Path]) -> None:
        """Save the vectorstore to the specified path
        
        Args:
            path: Save path
        """
        if self._vectorstore is None:
            raise RuntimeError("Vector storage not initialized")
        
        self._vectorstore.save(path)
    
    @classmethod
    def from_vectorstore(
        cls,
        vectorstore_path: Union[str, Path],
        api_key: Optional[str] = None,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4o",
        teacher_profile: Optional[TeacherProfile] = None,
        **kwargs
    ) -> "SimpleRAG":
        """Create an instance from an existing vectorstore
        
        Args:
            vectorstore_path: Path to the vectorstore
            api_key: API key
            llm_provider: LLM Provider
            llm_model: Model name
            teacher_profile: Teacher persona profile
            **kwargs: Additional configuration parameters
            
        Returns:
            SimpleRAG instance
        """
        instance = cls(
            api_key=api_key,
            llm_provider=llm_provider,
            llm_model=llm_model,
            teacher_profile=teacher_profile,
            vectorstore_path=str(vectorstore_path),
            **kwargs
        )
        return instance

