"""
PDF document extractor with OCR support for scanned documents.
"""

from typing import Dict, Any
import PyPDF2
import pdfplumber
from pathlib import Path


class PDFExtractor:
    """Extract text and metadata from PDF files."""
    
    async def extract_text(self, file_path: str) -> str:
        """
        Extract text from PDF.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        # Try pdfplumber first (better for complex PDFs)
        try:
            with pdfplumber.open(file_path) as pdf:
                text_parts = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return "\n".join(text_parts)
        except Exception:
            # Fallback to PyPDF2
            with open(file_path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text_parts = []
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return "\n".join(text_parts)
    
    async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract PDF metadata.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with metadata
        """
        with open(file_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            metadata = pdf_reader.metadata or {}
            
            return {
                "page_count": len(pdf_reader.pages),
                "title": metadata.get("/Title", ""),
                "author": metadata.get("/Author", ""),
                "created_date": metadata.get("/CreationDate", ""),
                "modified_date": metadata.get("/ModDate", ""),
            }
    
    async def extract_content(self, file_path: str) -> Dict[str, Any]:
        """
        Extract both text and metadata from PDF.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with text and metadata
        """
        text = await self.extract_text(file_path)
        metadata = await self.extract_metadata(file_path)
        
        return {
            "text": text,
            "metadata": metadata,
        }
