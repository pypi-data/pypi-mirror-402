"""Agentic RAG Implementation

An agent-based RAG implementation built on LangGraph,
Tool invocation, multi-step reasoning, and state persistence are supported.
"""

from pathlib import Path
from typing import Optional, Union, Literal
import uuid

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from edurag.config import EduRAGConfig
from edurag.prompt.teacher_profile import TeacherProfile
from edurag.llm.provider import create_llm, create_embeddings
from edurag.document.loader import DocumentLoader
from edurag.document.splitter import create_splitter
from edurag.vectorstore.faiss_store import FAISSVectorStore


class AgenticRAG:
    """Agentic RAG Implementation

    An agent-based RAG built on LangGraph, with the following differences from SimpleRAG:
    - The agent can autonomously decide whether retrieval is necessary
    - Supports multi-step reasoning (retrieve → analyze → retrieve again → answer)
    - Uses a state graph to manage the conversation flow
    - Better suited for handling complex queries

    Example:
        >>> from edurag import AgenticRAG, TeacherProfile
        >>> 
        >>> teacher = TeacherProfile(
        ...     name="Dr. Lee",
        ...     subject="AP Physics",
        ...     grade_level="Grade 10-12",
        ...     teaching_style="Detailed and patient, good at explaining physics concepts by examples from daily life."
        ... )
        >>> 
        >>> rag = AgenticRAG(
        ...     api_key="sk-xxx",
        ...     teacher_profile=teacher
        ... )
        >>> rag.load_documents(["AP Physics Textbook.pdf"])
        >>> 
        >>> answer = rag.ask("Compare the differences among three Newton's Laws of Motion.")
        >>> print(answer)
    
    Note:
        To use AgenticRAG, you need to install langgraph:
        pip install edurag[agentic]
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4o",
        teacher_profile: Optional[TeacherProfile] = None,
        config: Optional[EduRAGConfig] = None,
        thread_id: Optional[str] = None,
        **kwargs
    ):
        """Initialize AgenticRAG
        
        Args:
            api_key: LLM API key
            llm_provider: LLM provider (openai/gemini/ollama)
            llm_model: Model Name
            teacher_profile: Teacher persona configuration
            config: Full configuration object
            thread_id: Conversation thread ID for state persistence; automatically generated if None
            **kwargs: Additional configuration parameters
        """
        # checkout whether langgraph is installed
        try:
            from langgraph.checkpoint.memory import MemorySaver
            from langgraph.graph import END, START, StateGraph, MessagesState
            from langgraph.prebuilt import ToolNode
        except ImportError:
            raise ImportError(
                "While using AgenticRAG langgraph should be installed: "
                "pip install edurag[agentic] OR pip install langgraph"
            )
        
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
        self.thread_id = thread_id or str(uuid.uuid4())
        
        # Initialize Embeddings
        self._embeddings = create_embeddings(
            provider=self.config.llm_provider,
            model=self.config.embedding_model if self.config.llm_provider == "openai" else None,
            api_key=self.config.api_key,
            api_base=self.config.api_base
        )
        
        # Vector storage
        self._vectorstore: Optional[FAISSVectorStore] = None
        
        # LangGraph components (lazy initialization)
        self._app = None
        self._checkpointer = None
        
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
            sources: Document paths
            chunk_size: Chunk size for document splitting
            chunk_overlap: Overlap size between chunks
            
        Returns:
            Number of loaded document chunks
        """
        # Standardize Input
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
            raise ValueError("No documents loaded.")
        
        # Split the documents
        splitter = create_splitter(
            method="recursive",
            chunk_size=chunk_size or self.config.chunk_size,
            chunk_overlap=chunk_overlap or self.config.chunk_overlap
        )
        split_docs = splitter.split_documents(all_docs)
        
        # Build vector storage
        if self._vectorstore is None:
            self._vectorstore = FAISSVectorStore(self._embeddings)
        
        self._vectorstore.add_documents(split_docs)
        
        # Build Agent workflows
        self._build_agent()
        
        # Persistence
        if self.config.vectorstore_path:
            self._vectorstore.save(self.config.vectorstore_path)
        
        return len(split_docs)
    
    def _load_vectorstore(self, path: Path) -> None:
        """Load existing vectorstore"""
        self._vectorstore = FAISSVectorStore.from_local(path, self._embeddings)
        self._build_agent()
    
    def _build_agent(self) -> None:
        """Build LangGraph Agent workflow"""
        if self._vectorstore is None:
            return
        
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph.graph import END, START, StateGraph, MessagesState
        from langgraph.prebuilt import ToolNode
        
        # Create retrieval tools
        vectorstore = self._vectorstore
        top_k = self.config.retrieval_top_k
        
        @tool
        def retrieve_context(query: str) -> str:
            """Search for relevant documents in the knowledge base.
            
            Args:
                query: Search query describing what you want to find
                
            Returns:
                Concatenated text of the relevant document content
            """
            results = vectorstore.search(query, top_k=top_k)
            if not results:
                return "Did not find relevant documents."
            return "\n\n---\n\n".join([doc.page_content for doc in results])
        
        tools = [retrieve_context]
        tool_node = ToolNode(tools)
        
        # create LLM
        llm = create_llm(
            provider=self.config.llm_provider,
            model=self.config.llm_model,
            api_key=self.config.api_key,
            api_base=self.config.api_base,
            temperature=self.config.temperature
        )
        model_with_tools = llm.bind_tools(tools)
        
        # save the LLM with tools
        self._model_with_tools = model_with_tools
        
        # Decision function: whether to continue invoking tools
        def should_continue(state: MessagesState) -> Literal["tools", "__end__"]:
            messages = state['messages']
            last_message = messages[-1]
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tools"
            return END
        
        # call model
        def call_model(state: MessagesState):
            messages = state['messages']
            
            # If a teacher persona is provided, add a system message
            if self.teacher_profile and len(messages) > 0:
                # Check whether a system message already exists
                has_system = any(
                    isinstance(m, SystemMessage) for m in messages
                )
                if not has_system:
                    system_prompt = self.teacher_profile.to_system_prompt()
                    messages = [SystemMessage(content=system_prompt)] + list(messages)
            
            response = self._model_with_tools.invoke(messages)
            return {"messages": [response]}
        
        # build StateGraph
        workflow = StateGraph(MessagesState)
        
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", tool_node)
        
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", should_continue)
        workflow.add_edge("tools", "agent")
        
        # Configure a memory checkpointer
        self._checkpointer = MemorySaver()
        
        # Compile workflow
        self._app = workflow.compile(checkpointer=self._checkpointer)
    
    def ask(self, question: str) -> str:
        """Ask a question and get an answer
        
        Args:
            question: User question
            
        Returns:
            AI generated answer
        """
        if self._app is None:
            raise RuntimeError(
                "The knowledge base has not been initialized. Please call load_documents() to load documents first."
            )
        
        # build messages
        messages = [HumanMessage(content=question)]
        
        # Execute workflow
        final_state = self._app.invoke(
            {"messages": messages},
            config={"configurable": {"thread_id": self.thread_id}}
        )
        
        # Get final responses
        return final_state["messages"][-1].content
    
    def ask_with_steps(self, question: str) -> dict:
        """Ask a question and return the complete reasoning process
        
        Args:
            question: User question
            
        Returns:
            A dictionary containing `answer` and `steps`
        """
        if self._app is None:
            raise RuntimeError(
                "The knowledge base has not been initialized. Please call load_documents() to load documents first."
            )
        
        messages = [HumanMessage(content=question)]
        
        final_state = self._app.invoke(
            {"messages": messages},
            config={"configurable": {"thread_id": self.thread_id}}
        )
        
        # Parse steps
        steps = []
        for msg in final_state["messages"]:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tc in msg.tool_calls:
                    steps.append({
                        "type": "tool_call",
                        "tool": tc["name"],
                        "input": tc["args"]
                    })
            elif hasattr(msg, 'type') and msg.type == "tool":
                steps.append({
                    "type": "tool_result",
                    "content": msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
                })
        
        return {
            "answer": final_state["messages"][-1].content,
            "steps": steps,
            "total_messages": len(final_state["messages"])
        }
    
    def search(self, query: str, top_k: int = 4) -> list[Document]:
        """Directly search for relevant documents
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of relevant documents
        """
        if self._vectorstore is None:
            raise RuntimeError("The knowledge base has not been initialized.")
        
        return self._vectorstore.search(query, top_k=top_k)
    
    def new_conversation(self, thread_id: Optional[str] = None) -> str:
        """Start a new conversation (generate a new thread_id)
        
        Args:
            thread_id: Specify a new thread ID; automatically generated if None
            
        Returns:
            The new thread_id
        """
        self.thread_id = thread_id or str(uuid.uuid4())
        return self.thread_id
    
    def save_vectorstore(self, path: Union[str, Path]) -> None:
        """Save the vector store
        
        Args:
            path: Save path
        """
        if self._vectorstore is None:
            raise RuntimeError("The vectorstore has not been initialized.")
        
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
    ) -> "AgenticRAG":
        """Create an instance from an existing vectorstore
        
        Args:
            vectorstore_path: Path to the vectorstore
            api_key: API key
            llm_provider: LLM provider
            llm_model: Model name
            teacher_profile: Teacher persona profile
            **kwargs: Additional configuration parameters
            
        Returns:
            AgenticRAG instance
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

