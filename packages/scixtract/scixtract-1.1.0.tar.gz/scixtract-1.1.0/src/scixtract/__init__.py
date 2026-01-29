"""
AI-Powered PDF Text Extraction and Knowledge Indexing

A comprehensive library for extracting text from academic PDFs using AI,
with advanced knowledge tracking and search capabilities.

Author: Reto Stamm
Email: reto.stamm@ul.ie
"""

__version__ = "1.1.0"
__author__ = "Reto Stamm"
__email__ = "reto.stamm@ul.ie"

from .extractor import AdvancedPDFProcessor, OllamaAIProcessor
from .knowledge import KnowledgeTracker
from .models import DocumentMetadata, ExtractionResult, PageContent

__all__ = [
    "AdvancedPDFProcessor",
    "OllamaAIProcessor",
    "KnowledgeTracker",
    "DocumentMetadata",
    "PageContent",
    "ExtractionResult",
]
