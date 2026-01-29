"""
Plain text and markup file extractor for TXT, MD, HTML, XML, JSON files.
"""

from typing import Dict, Any
import aiofiles
import json
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path


class TextExtractor:
    """Extract content from text-based files."""
    
    async def extract_text(self, file_path: str) -> str:
        """
        Extract text from text file.
        
        Args:
            file_path: Path to text file
            
        Returns:
            Extracted text content
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix == ".json":
            return await self._extract_json(file_path)
        elif suffix in [".xml", ".html", ".htm"]:
            return await self._extract_markup(file_path)
        else:
            # Plain text, markdown, etc.
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                return await f.read()
    
    async def _extract_json(self, file_path: str) -> str:
        """Extract text from JSON file."""
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()
            try:
                data = json.loads(content)
                return json.dumps(data, indent=2)
            except json.JSONDecodeError:
                return content
    
    async def _extract_markup(self, file_path: str) -> str:
        """Extract text from HTML/XML file."""
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix in [".html", ".htm"]:
            return await self._extract_html_text(file_path)
        else:  # XML
            return await self._extract_xml_text(file_path)
    
    async def _extract_html_text(self, file_path: str) -> str:
        """Extract text from HTML file."""
        class HTMLTextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text_parts = []
            
            def handle_data(self, data):
                if data.strip():
                    self.text_parts.append(data.strip())
        
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()
            parser = HTMLTextExtractor()
            parser.feed(content)
            return " ".join(parser.text_parts)
    
    async def _extract_xml_text(self, file_path: str) -> str:
        """Extract text from XML file."""
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        def get_text(element):
            text_parts = []
            if element.text:
                text_parts.append(element.text.strip())
            for child in element:
                text_parts.extend(get_text(child))
            if element.tail:
                text_parts.append(element.tail.strip())
            return text_parts
        
        text_parts = get_text(root)
        return " ".join(filter(None, text_parts))
    
    async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from text file.
        
        Args:
            file_path: Path to text file
            
        Returns:
            Dictionary with metadata
        """
        return {
            "title": "",
            "author": "",
            "created_date": "",
            "modified_date": "",
        }
    
    async def extract_content(self, file_path: str) -> Dict[str, Any]:
        """
        Extract both text and metadata from text file.
        
        Args:
            file_path: Path to text file
            
        Returns:
            Dictionary with text and metadata
        """
        text = await self.extract_text(file_path)
        metadata = await self.extract_metadata(file_path)
        
        return {
            "text": text,
            "metadata": metadata,
        }
