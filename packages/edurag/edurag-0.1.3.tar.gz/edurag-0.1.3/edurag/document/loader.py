"""Document Loader

A unified loading interface that supports multiple document formats.
"""

from pathlib import Path
from typing import Union, Optional
from langchain_core.documents import Document


class DocumentLoader:
    """Multi-format Document Loader
    
    Supports common document formats such as PDF, DOCX, DOC, and TXT.
    
    Example:
        >>> loader = DocumentLoader()
        >>> docs = loader.load("textbook.pdf")
        >>> docs = loader.load_directory("./documents", extensions=[".pdf", ".docx"])
    """
    
    # Supported file formats and their loaders
    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}
    
    @classmethod
    def load(cls, file_path: Union[str, Path]) -> list[Document]:
        """Load single document
        
        Args:
            file_path: Path of the document
            
        Returns:
            Document list
            
        Raises:
            FileNotFoundError: The file doesn't exist
            ValueError: Unsupported format of the document
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"The file does not exist: {path}")
        
        ext = path.suffix.lower()
        
        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported document format: {ext}。"
                f"Supported formats of documents: {', '.join(cls.SUPPORTED_EXTENSIONS)}"
            )
        
        return cls._load_by_extension(path, ext)
    
    @classmethod
    def _load_by_extension(cls, path: Path, ext: str) -> list[Document]:
        """Select the loader based on the file extension"""
        
        if ext == ".pdf":
            from langchain_community.document_loaders import PyPDFLoader
            loader = PyPDFLoader(str(path))
            return loader.load()
        
        elif ext in (".docx", ".doc"):
            try:
                from langchain_community.document_loaders import Docx2txtLoader
                loader = Docx2txtLoader(str(path))
                return loader.load()
            except ImportError:
                raise ImportError(
                    "docx2txt should be installed while loading doc, docx files: pip install docx2txt"
                )
        
        elif ext == ".txt":
            from langchain_community.document_loaders import TextLoader
            loader = TextLoader(str(path), encoding="utf-8")
            return loader.load()
        
        elif ext == ".md":
            from langchain_community.document_loaders import TextLoader
            loader = TextLoader(str(path), encoding="utf-8")
            return loader.load()
        
        else:
            raise ValueError(f"Unknown file extension: {ext}")
    
    @classmethod
    def load_multiple(cls, file_paths: list[Union[str, Path]]) -> list[Document]:
        """Load multiple documents in batch
        
        Args:
            file_paths: Documents path list
            
        Returns:
            The path list of all documents
        """
        all_docs = []
        for path in file_paths:
            docs = cls.load(path)
            all_docs.extend(docs)
        return all_docs
    
    @classmethod
    def load_directory(
        cls,
        dir_path: Union[str, Path],
        extensions: Optional[list[str]] = None,
        recursive: bool = True
    ) -> list[Document]:
        """Load all documents in a directory
        
        Args:
            dir_path: Directory path
            extensions: List of file extensions to load; loads all supported formats if None
            recursive: Whether to recursively load subdirectories
            
        Returns:
            List of Document objects for all loaded documents
        """
        path = Path(dir_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Path doesn't exist: {path}")
        
        if not path.is_dir():
            raise ValueError(f"Directory is not the path: {path}")
        
        extensions = extensions or list(cls.SUPPORTED_EXTENSIONS)
        # Normalize file extension format
        extensions = [ext if ext.startswith(".") else f".{ext}" for ext in extensions]
        
        all_docs = []
        pattern = "**/*" if recursive else "*"
        
        for ext in extensions:
            for file_path in path.glob(f"{pattern}{ext}"):
                if file_path.is_file():
                    try:
                        docs = cls.load(file_path)
                        all_docs.extend(docs)
                    except Exception as e:
                        # Log errors and continue processing other files
                        print(f"Warning: Load {file_path} error: {e}")
        
        return all_docs

