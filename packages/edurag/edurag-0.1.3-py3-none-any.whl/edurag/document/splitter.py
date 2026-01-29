"""Text Splitter"""

from typing import Literal
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
)
from langchain_core.documents import Document


def create_splitter(
    method: Literal["character", "recursive", "token"] = "recursive",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    **kwargs
):
    """Create a text splitter
    
    Args:
        method: Splitting method
            - "character": Split by character count (simple and fast)
            - "recursive": Recursive splitting (recommended; preserves semantic integrity)
            - "token": Split by token count (aligned with LLM token limits)
        chunk_size: Chunk size
        chunk_overlap: Overlap size between chunks
        **kwargs: Additional parameters passed to the specific splitter
        
    Returns:
        TextSplitter instance
        
    Example:
        >>> splitter = create_splitter("recursive", chunk_size=500)
        >>> chunks = splitter.split_documents(docs)
    """
    
    if method == "character":
        return CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            **kwargs
        )
    
    elif method == "recursive":
        # 针对中文优化的分隔符
        separators = kwargs.pop("separators", None)
        if separators is None:
            separators = [
                "\n\n",      # 段落
                "\n",        # 换行
                "。",        # 中文句号
                "！",        # 中文感叹号
                "？",        # 中文问号
                "；",        # 中文分号
                "，",        # 中文逗号
                ".",         # 英文句号
                "!",         # 英文感叹号
                "?",         # 英文问号
                ";",         # 英文分号
                ",",         # 英文逗号
                " ",         # 空格
                "",          # 字符
            ]
        
        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            **kwargs
        )
    
    elif method == "token":
        return TokenTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            **kwargs
        )
    
    else:
        raise ValueError(
            f"Unsupported splitting method: {method}。"
            f"Supported options: character, recursive, token"
        )


def split_documents(
    documents: list[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    method: Literal["character", "recursive", "token"] = "recursive",
) -> list[Document]:
    """Convenience function: split a list of documents
    
    Args:
        documents: List of documents to be split
        chunk_size: Chunk size
        chunk_overlap: Overlap size between chunks
        method: Splitting method
        
    Returns:
        List of split documents
    """
    splitter = create_splitter(method, chunk_size, chunk_overlap)
    return splitter.split_documents(documents)

