"""FAISS Vector Store"""

from pathlib import Path
from typing import Optional, Union
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import FAISS


class FAISSVectorStore:
    """FAISS Vector Store Wrapper

    Provides a unified interface for document vectorization, storage, and retrieval.

    Example:
        >>> from edurag.llm import create_embeddings
        >>> embeddings = create_embeddings("openai", api_key="sk-xxx")
        >>> store = FAISSVectorStore(embeddings)
        >>> store.add_documents(docs)
        >>> results = store.search("The 2nd Newton's Law of Motion", top_k=3)
    """
    
    def __init__(self, embeddings: Embeddings):
        """Initialize the vector store
        
        Args:
            embeddings: Embeddings instance used for text vectorization
        """
        self.embeddings = embeddings
        self._vectorstore: Optional[FAISS] = None
    
    @property
    def is_initialized(self) -> bool:
        """Check whether the vector store has been initialized"""
        return self._vectorstore is not None
    
    def add_documents(self, documents: list[Document]) -> None:
        """Add documents to the vector store
        
        Args:
            documents: document list
        """
        if not documents:
            raise ValueError("The document list cannot be empty")
        
        if self._vectorstore is None:
            # create a new vectorstore
            self._vectorstore = FAISS.from_documents(documents, self.embeddings)
        else:
            # Append to the existing vectorstore
            self._vectorstore.add_documents(documents)
    
    def search(
        self,
        query: str,
        top_k: int = 4,
        score_threshold: Optional[float] = None
    ) -> list[Document]:
        """Similarity search
        
        Args:
            query: Query text
            top_k: Number of results to return
            score_threshold: Similarity threshold (optional)
            
        Returns:
            List of relevant documents
        """
        if not self.is_initialized:
            raise RuntimeError("The vector store has not been initialized. Please call 'add_documents' first")
        
        if score_threshold is not None:
            # Search with similarity score filtering
            docs_with_scores = self._vectorstore.similarity_search_with_score(
                query, k=top_k
            )
            # Filter out results below the threshold (note: FAISS returns distances, where smaller values indicate higher similarity).
            return [doc for doc, score in docs_with_scores if score <= score_threshold]
        else:
            return self._vectorstore.similarity_search(query, k=top_k)
    
    def search_with_scores(
        self,
        query: str,
        top_k: int = 4
    ) -> list[tuple[Document, float]]:
        """Search with similarity scores
        
        Args:
            query: Query text
            top_k: Number of results to return
            
        Returns:
            List of (document, score) tuples
        """
        if not self.is_initialized:
            raise RuntimeError("The vector store has not been initialized. Please call 'add_documents' first")
        
        return self._vectorstore.similarity_search_with_score(query, k=top_k)
    
    def as_retriever(self, top_k: int = 4, **kwargs):
        """Convert to LangChain Retriever
        
        Args:
            top_k: Number of retrieval results
            **kwargs: Additional retriever parameters
            
        Returns:
            VectorStoreRetriever instance
        """
        if not self.is_initialized:
            raise RuntimeError("The vector store has not been initialized. Please call 'add_documents' first")
        
        return self._vectorstore.as_retriever(
            search_kwargs={"k": top_k, **kwargs}
        )
    
    def save(self, path: Union[str, Path]) -> None:
        """Save the vector store to local path
        
        Args:
            path: Save path
        """
        if not self.is_initialized:
            raise RuntimeError("The vector store has not been initialized and cannot be saved")
        
        self._vectorstore.save_local(str(path))
    
    def load(self, path: Union[str, Path]) -> None:
        """Load the vector store from local path
        
        Args:
            path: Save path
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Vector storage path doesn't exist: {path}")
        
        self._vectorstore = FAISS.load_local(
            str(path),
            self.embeddings,
            allow_dangerous_deserialization=True
        )
    
    @classmethod
    def from_documents(
        cls,
        documents: list[Document],
        embeddings: Embeddings
    ) -> "FAISSVectorStore":
        """Create a vector store from a list of documents

        Args:
            documents: List of documents
            embeddings: Embeddings instance

        Returns:
            FAISSVectorStore instance
        """
        store = cls(embeddings)
        store.add_documents(documents)
        return store
    
    @classmethod
    def from_local(
        cls,
        path: Union[str, Path],
        embeddings: Embeddings
    ) -> "FAISSVectorStore":
        """Load a vector store from local storage

        Args:
            path: Storage path
            embeddings: Embeddings instance

        Returns:
            FAISSVectorStore instance
        """
        store = cls(embeddings)
        store.load(path)
        return store

