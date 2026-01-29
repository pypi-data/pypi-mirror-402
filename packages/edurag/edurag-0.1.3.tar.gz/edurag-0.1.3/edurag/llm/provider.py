"""LLM Provider interface

A unified interface wrapper that supports multiple LLM providers.
"""

from typing import Literal, Optional, Any
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings


def create_llm(
    provider: Literal["openai", "gemini", "ollama"],
    model: str,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    temperature: float = 0.7,
    **kwargs: Any
) -> BaseChatModel:
    """Create an LLM instance

    Args:
        provider: LLM provider (openai / gemini / ollama)
        model: Model name
        api_key: API key
        api_base: Custom API endpoint
        temperature: Generation temperature
        **kwargs: Additional model parameters

    Returns:
        BaseChatModel: A LangChain-compatible LLM instance

    Raises:
        ValueError: Unsupported provider
        ImportError: Missing dependency package for the specified provider
        
    Example:
        >>> llm = create_llm("openai", "gpt-4o", api_key="sk-xxx")
        >>> llm = create_llm("ollama", "llama3")  # No api_key requirements for local deployment
    """
    
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        
        init_kwargs = {
            "model": model,
            "temperature": temperature,
            **kwargs
        }
        if api_key:
            init_kwargs["api_key"] = api_key
        if api_base:
            init_kwargs["base_url"] = api_base
            
        return ChatOpenAI(**init_kwargs)
    
    elif provider == "gemini":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ImportError(
                "While using Gemini, you should install langchain-google-genai: "
                "pip install edurag[gemini]"
            )
        
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature,
            **kwargs
        )
    
    elif provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            raise ImportError(
                "While using Ollama, you should install langchain-ollama: "
                "pip install edurag[ollama]"
            )
        
        init_kwargs = {
            "model": model,
            "temperature": temperature,
            **kwargs
        }
        if api_base:
            init_kwargs["base_url"] = api_base
            
        return ChatOllama(**init_kwargs)
    
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}。"
            f"Supported LLMs: openai, gemini, ollama"
        )


def create_embeddings(
    provider: Literal["openai", "gemini", "ollama"] = "openai",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    **kwargs: Any
) -> Embeddings:
    """Create an Embeddings instance

    Args:
        provider: Provider (openai/gemini/ollama)
        model: Embedding model name; if None, the default model is used
        api_key: API key
        api_base: Custom API endpoint
        **kwargs: Other parameters
        
    Returns:
        Embeddings: LangChain-compatible Embeddings instances
    """
    
    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        
        init_kwargs = {**kwargs}
        if model:
            init_kwargs["model"] = model
        if api_key:
            init_kwargs["api_key"] = api_key
        if api_base:
            init_kwargs["base_url"] = api_base
            
        return OpenAIEmbeddings(**init_kwargs)
    
    elif provider == "gemini":
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
        except ImportError:
            raise ImportError(
                "While using Gemini Embeddings you should install: pip install edurag[gemini]"
            )
        
        return GoogleGenerativeAIEmbeddings(
            model=model or "models/embedding-001",
            google_api_key=api_key,
            **kwargs
        )
    
    elif provider == "ollama":
        try:
            from langchain_ollama import OllamaEmbeddings
        except ImportError:
            raise ImportError(
                "While using Ollama Embeddings you should install: pip install edurag[ollama]"
            )
        
        init_kwargs = {"model": model or "nomic-embed-text", **kwargs}
        if api_base:
            init_kwargs["base_url"] = api_base
            
        return OllamaEmbeddings(**init_kwargs)
    
    else:
        raise ValueError(f"Unsupported Embeddings provider: {provider}")

