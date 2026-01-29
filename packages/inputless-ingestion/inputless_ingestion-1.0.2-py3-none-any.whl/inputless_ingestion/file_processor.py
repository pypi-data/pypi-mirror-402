"""
File processor for handling multiple document formats.

Main orchestrator for document processing pipeline.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import aiofiles
import chardet
from pydantic import BaseModel

# Optional python-magic import (requires system libmagic)
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    magic = None

from .models import DocumentData, DocumentMetadata
from .exceptions import UnsupportedFileTypeError, ProcessingError
from .ocr_engine import OCREngine
from .nlp_processor import NLPProcessor
from .ai_extractor import AIKnowledgeExtractor
from .extractors.pdf_extractor import PDFExtractor
from .extractors.docx_extractor import DOCXExtractor
from .extractors.text_extractor import TextExtractor
from .extractors.image_extractor import ImageExtractor


class DocumentProcessor:
    """
    Main document processing orchestrator.
    
    Coordinates file type detection, format-specific extraction,
    OCR processing, NLP analysis, and AI knowledge extraction.
    """
    
    def __init__(
        self,
        enable_ocr: bool = True,
        enable_nlp: bool = True,
        enable_ai: bool = True,
        ocr_confidence_threshold: float = 0.7,
    ):
        """
        Initialize document processor.
        
        Args:
            enable_ocr: Enable OCR processing for images/scanned docs
            enable_nlp: Enable NLP processing
            enable_ai: Enable AI knowledge extraction
            ocr_confidence_threshold: Minimum OCR confidence threshold
        """
        self.enable_ocr = enable_ocr
        self.enable_nlp = enable_nlp
        self.enable_ai = enable_ai
        self.ocr_confidence_threshold = ocr_confidence_threshold
        
        # Initialize components
        self.ocr_engine = OCREngine() if enable_ocr else None
        self.nlp_processor = NLPProcessor() if enable_nlp else None
        self.ai_extractor = AIKnowledgeExtractor() if enable_ai else None
        
        # Format extractors
        self.extractors = {
            "pdf": PDFExtractor(),
            "docx": DOCXExtractor(),
            "txt": TextExtractor(),
            "image": ImageExtractor(),
        }
    
    async def process_file(
        self,
        file_path: str,
        extract_entities: bool = True,
        extract_topics: bool = True,
        extract_ai_insights: bool = True,
    ) -> DocumentData:
        """
        Process a single document file.
        
        Args:
            file_path: Path to document file
            extract_entities: Extract entities using NLP
            extract_topics: Extract topics using NLP
            extract_ai_insights: Extract AI insights
            
        Returns:
            DocumentData with extracted text, metadata, and analysis
            
        Raises:
            UnsupportedFileTypeError: If file type is not supported
            FileNotFoundError: If file does not exist
            ProcessingError: If processing fails
        """
        try:
            # Validate file exists
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Detect file type
            file_type = await self._detect_file_type(file_path)
            
            if file_type not in self.extractors:
                raise UnsupportedFileTypeError(f"Unsupported file type: {file_type}")
            
            # Extract metadata
            metadata = await self._extract_metadata(file_path, file_type)
            
            # Extract text using format-specific extractor
            extractor = self.extractors[file_type]
            content = await extractor.extract_content(file_path)
            text = content.get("text", "")
            
            # OCR processing if needed (for images or scanned PDFs)
            ocr_confidence = None
            if self.enable_ocr and file_type in ["image", "pdf"]:
                # Check if OCR is needed (low text confidence or image file)
                if file_type == "image" or await self._needs_ocr(file_path, text):
                    if self.ocr_engine:
                        ocr_result = await self.ocr_engine.process_image(file_path)
                        if ocr_result.confidence >= self.ocr_confidence_threshold:
                            text = ocr_result.text
                            ocr_confidence = ocr_result.confidence
            
            # NLP processing
            entities = None
            topics = None
            if self.enable_nlp and text and self.nlp_processor:
                if extract_entities:
                    entities_list = await self.nlp_processor.extract_entities(text)
                    entities = [e.dict() for e in entities_list] if entities_list else None
                if extract_topics:
                    topics_list = await self.nlp_processor.extract_topics(text)
                    topics = [t.dict() for t in topics_list] if topics_list else None
            
            # AI knowledge extraction
            ai_insights = None
            if self.enable_ai and text and extract_ai_insights:
                if self.ai_extractor:
                    knowledge = await self.ai_extractor.extract_knowledge(
                        text, document_type=file_type
                    )
                    ai_insights = knowledge.dict()
            
            return DocumentData(
                text=text,
                metadata=metadata,
                entities=entities,
                topics=topics,
                ai_insights=ai_insights,
                ocr_confidence=ocr_confidence,
            )
        except (UnsupportedFileTypeError, FileNotFoundError):
            raise
        except Exception as e:
            raise ProcessingError(f"Document processing failed: {str(e)}") from e
    
    async def process_batch(
        self,
        file_paths: List[str],
        max_concurrent: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Process multiple documents in batch.
        
        Args:
            file_paths: List of file paths to process
            max_concurrent: Maximum concurrent processing tasks
            
        Returns:
            List of processing results (success or error)
        """
        import asyncio
        
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []
        
        async def process_with_semaphore(file_path: str):
            async with semaphore:
                try:
                    data = await self.process_file(file_path)
                    return {
                        "file": file_path,
                        "status": "success",
                        "data": data.dict(),
                    }
                except Exception as e:
                    return {
                        "file": file_path,
                        "status": "error",
                        "error": str(e),
                    }
        
        tasks = [process_with_semaphore(fp) for fp in file_paths]
        results = await asyncio.gather(*tasks)
        
        return results
    
    async def _detect_file_type(self, file_path: str) -> str:
        """Detect file type from file path and content."""
        # Use python-magic for MIME type detection
        mime_type = None
        if MAGIC_AVAILABLE:
            try:
                mime = magic.Magic(mime=True)
                mime_type = mime.from_file(file_path)
            except Exception:
                mime_type = None
        
        # Map MIME type to file type
        mime_to_type = {
            "application/pdf": "pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
            "application/msword": "docx",
            "text/plain": "txt",
            "text/html": "html",
            "application/xml": "xml",
            "application/json": "json",
            "image/jpeg": "image",
            "image/png": "image",
            "image/tiff": "image",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "excel",
            "application/vnd.ms-excel": "excel",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
        }
        
        file_type = mime_to_type.get(mime_type) if mime_type else None
        
        # Fallback to extension-based detection
        if not file_type:
            ext = Path(file_path).suffix.lower()
            ext_to_type = {
                ".pdf": "pdf",
                ".docx": "docx",
                ".doc": "docx",
                ".txt": "txt",
                ".html": "html",
                ".htm": "html",
                ".xml": "xml",
                ".json": "json",
                ".jpg": "image",
                ".jpeg": "image",
                ".png": "image",
                ".tiff": "image",
                ".bmp": "image",
                ".xlsx": "excel",
                ".xls": "excel",
                ".pptx": "pptx",
                ".ppt": "pptx",
            }
            file_type = ext_to_type.get(ext, "txt")
        
        return file_type
    
    async def _extract_metadata(
        self, file_path: str, file_type: str
    ) -> DocumentMetadata:
        """Extract document metadata."""
        path = Path(file_path)
        stat = path.stat()
        
        # Get MIME type
        mime_type = "application/octet-stream"
        if MAGIC_AVAILABLE:
            try:
                mime = magic.Magic(mime=True)
                mime_type = mime.from_file(file_path)
            except Exception:
                mime_type = "application/octet-stream"
        
        # Detect encoding for text files
        encoding = None
        if file_type in ["txt", "html", "xml"]:
            try:
                async with aiofiles.open(file_path, "rb") as f:
                    raw_data = await f.read(10000)  # Read first 10KB
                    detected = chardet.detect(raw_data)
                    encoding = detected.get("encoding")
            except Exception:
                encoding = "utf-8"
        
        # Extract format-specific metadata
        format_metadata = {}
        metadata_extractor = self.extractors.get(file_type)
        if metadata_extractor:
            try:
                format_metadata = await metadata_extractor.extract_metadata(file_path)
            except Exception:
                format_metadata = {}
        
        return DocumentMetadata(
            file_path=str(file_path),
            file_type=file_type,
            file_size=stat.st_size,
            mime_type=mime_type,
            encoding=encoding,
            **format_metadata,
        )
    
    async def _needs_ocr(self, file_path: str, extracted_text: str) -> bool:
        """Check if OCR is needed (low text content)."""
        # If extracted text is very short, likely needs OCR
        if len(extracted_text.strip()) < 100:
            return True
        
        # Check if text looks like placeholder or error
        if "error" in extracted_text.lower() or "unable" in extracted_text.lower():
            return True
        
        return False
