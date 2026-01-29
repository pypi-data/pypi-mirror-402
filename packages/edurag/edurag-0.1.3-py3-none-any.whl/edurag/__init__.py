"""
EduRAG:
An LLM-based Retrieval-Augmented Generation (RAG) component for education, supporting problem solving, academic literature analysis, and knowledge Q&A.
"""

from edurag.core.simple_rag import SimpleRAG
from edurag.core.agentic_rag import AgenticRAG
from edurag.prompt.teacher_profile import TeacherProfile
from edurag.config import EduRAGConfig

__version__ = "0.1.3"
__all__ = [
    "SimpleRAG",
    "AgenticRAG",
    "TeacherProfile", 
    "EduRAGConfig",
    "__version__",
]

