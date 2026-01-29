"""
inputless-ingestion - Document processing and knowledge extraction

Main module for document processing, OCR, NLP, and AI-powered knowledge extraction.
"""

from .file_processor import DocumentProcessor
from .ocr_engine import OCREngine
from .nlp_processor import NLPProcessor
from .ai_extractor import AIKnowledgeExtractor

# Optional graph integration
try:
    from .graph_integration import DocumentGraphIntegration
except ImportError:
    DocumentGraphIntegration = None

# Models
from .models import (
    DocumentData,
    DocumentMetadata,
    OCRResult,
    Entity,
    Topic,
    KnowledgeExtraction,
)

# Exceptions
from .exceptions import (
    IngestionError,
    UnsupportedFileTypeError,
    OCRProcessingError,
    NLPProcessingError,
    GraphIntegrationError,
    ProcessingError,
)

__version__ = "1.0.0"

# Build __all__ list conditionally
__all__ = [
    # Main classes
    "DocumentProcessor",
    "OCREngine",
    "NLPProcessor",
    "AIKnowledgeExtractor",
]

# Add DocumentGraphIntegration if available
if DocumentGraphIntegration is not None:
    __all__.append("DocumentGraphIntegration")

__all__.extend([
    # Models
    "DocumentData",
    "DocumentMetadata",
    "OCRResult",
    "Entity",
    "Topic",
    "KnowledgeExtraction",
    # Exceptions
    "IngestionError",
    "UnsupportedFileTypeError",
    "OCRProcessingError",
    "NLPProcessingError",
    "GraphIntegrationError",
    "ProcessingError",
])
