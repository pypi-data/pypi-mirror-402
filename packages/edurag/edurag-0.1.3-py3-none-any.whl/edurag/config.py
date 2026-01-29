"""EduRAG Global Configuration"""

from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class EduRAGConfig:
    """EduRAG Configuration Class
    
    Attributes:
        llm_provider: LLM provider，supports openai/gemini/ollama
        llm_model: Model name，e.g., gpt-4o, gemini-pro, llama3
        api_key: API key (can be None when using a local Ollama deployment)
        api_base: Base API URL for custom endpoints or proxies
        temperature: Generation temperature, between 0 and 1
        chunk_size: Document chunk size
        chunk_overlap: Overlap size between document chunks
        embedding_model: Embedding model name
        vectorstore_path: Path for vector store persistence (None disables persistence)
    """
    
    # LLM configuration
    llm_provider: Literal["openai", "gemini", "ollama"] = "openai"
    llm_model: str = "gpt-4o"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.7
    
    # Document processing configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Embedding configuration
    embedding_model: str = "text-embedding-3-small"
    
    # Vectorstore configuration
    vectorstore_path: Optional[str] = None
    
    # Retrieval configuration
    retrieval_top_k: int = 4
    
    def __post_init__(self):
        """Validate configuration"""
        if self.llm_provider in ("openai", "gemini") and not self.api_key:
            raise ValueError(f"{self.llm_provider} api_key must be provided")
        
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must greater than 0")
        
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must smaller than chunk_size")

