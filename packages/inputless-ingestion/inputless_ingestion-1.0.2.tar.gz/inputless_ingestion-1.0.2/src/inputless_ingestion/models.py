"""
Pydantic models for ingestion module.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DocumentMetadata(BaseModel):
    """Document metadata."""
    file_path: str
    file_type: str
    file_size: int
    mime_type: str
    encoding: Optional[str] = None
    page_count: Optional[int] = None
    author: Optional[str] = None
    title: Optional[str] = None
    created_date: Optional[str] = None
    modified_date: Optional[str] = None


class DocumentData(BaseModel):
    """Processed document data."""
    text: str
    metadata: DocumentMetadata
    entities: Optional[List[Dict[str, Any]]] = None
    topics: Optional[List[Dict[str, Any]]] = None
    ai_insights: Optional[Dict[str, Any]] = None
    ocr_confidence: Optional[float] = None


class OCRResult(BaseModel):
    """OCR processing result."""
    text: str
    confidence: float
    language: str
    provider: str


class Entity(BaseModel):
    """Named entity."""
    text: str
    label: str
    start: int
    end: int
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class Topic(BaseModel):
    """Document topic."""
    topic_id: int
    keywords: List[str]
    weight: float = Field(ge=0.0, le=1.0)


class KnowledgeExtraction(BaseModel):
    """AI-extracted knowledge."""
    summary: str
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)
    key_points: List[str] = Field(default_factory=list)

