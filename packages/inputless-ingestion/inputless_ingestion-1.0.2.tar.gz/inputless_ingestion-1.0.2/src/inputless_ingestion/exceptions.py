"""
Exception classes for ingestion module.
"""


class IngestionError(Exception):
    """Base exception for ingestion errors."""
    pass


class UnsupportedFileTypeError(IngestionError):
    """Raised when file type is not supported."""
    pass


class OCRProcessingError(IngestionError):
    """Raised when OCR processing fails."""
    pass


class NLPProcessingError(IngestionError):
    """Raised when NLP processing fails."""
    pass


class GraphIntegrationError(IngestionError):
    """Raised when graph integration fails."""
    pass


class ProcessingError(IngestionError):
    """Raised when document processing fails."""
    pass

