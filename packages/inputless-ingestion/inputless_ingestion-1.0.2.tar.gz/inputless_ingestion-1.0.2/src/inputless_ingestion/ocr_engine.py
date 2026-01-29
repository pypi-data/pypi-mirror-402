"""
OCR engine for extracting text from images and scanned documents.

Supports Tesseract OCR with image preprocessing for better accuracy.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import pytesseract
from PIL import Image
import cv2
import numpy as np

# Optional EasyOCR import
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    easyocr = None

from .models import OCRResult
from .exceptions import OCRProcessingError


class OCREngine:
    """
    OCR engine for text extraction from images and scanned documents.
    
    Supports Tesseract and EasyOCR with automatic fallback.
    """
    
    def __init__(
        self,
        language: str = "eng",
        provider: str = "tesseract",
        enable_preprocessing: bool = True,
    ):
        """
        Initialize OCR engine.
        
        Args:
            language: OCR language code (e.g., 'eng', 'spa', 'fra')
            provider: OCR provider ('tesseract', 'easyocr', or 'auto')
            enable_preprocessing: Enable image preprocessing
        """
        self.language = language
        self.provider = provider
        self.enable_preprocessing = enable_preprocessing
        
        # Initialize EasyOCR reader if needed
        self.easyocr_reader = None
        if (provider == "easyocr" or provider == "auto") and EASYOCR_AVAILABLE:
            try:
                self.easyocr_reader = easyocr.Reader([language])
            except Exception as e:
                # EasyOCR not available, will fallback to Tesseract
                print(f"Warning: EasyOCR initialization failed: {e}")
        elif provider == "easyocr" and not EASYOCR_AVAILABLE:
            raise ValueError(
                "EasyOCR is not installed. Install it with: pip install easyocr"
            )
    
    async def process_image(
        self, image_path: str, use_preprocessing: Optional[bool] = None
    ) -> OCRResult:
        """
        Process image with OCR.
        
        Args:
            image_path: Path to image file
            use_preprocessing: Override preprocessing setting
            
        Returns:
            OCRResult with extracted text and confidence
            
        Raises:
            OCRProcessingError: If OCR processing fails
        """
        try:
            # Load and preprocess image
            image = await self._load_image(image_path)
            
            use_preprocessing = (
                use_preprocessing if use_preprocessing is not None
                else self.enable_preprocessing
            )
            
            if use_preprocessing:
                image = await self._preprocess_image(image)
            
            # Perform OCR
            if self.provider == "tesseract":
                result = await self._tesseract_ocr(image)
            elif self.provider == "easyocr":
                result = await self._easyocr_ocr(image)
            else:  # auto
                # Try Tesseract first, fallback to EasyOCR
                try:
                    result = await self._tesseract_ocr(image)
                except Exception:
                    if self.easyocr_reader is None:
                        raise OCRProcessingError("No OCR provider available")
                    result = await self._easyocr_ocr(image)
            
            return result
        except Exception as e:
            raise OCRProcessingError(f"OCR processing failed: {str(e)}") from e
    
    async def process_with_confidence(
        self, image_path: str
    ) -> Dict[str, Any]:
        """
        Process image and return detailed confidence metrics.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with text, confidence, and metrics
        """
        result = await self.process_image(image_path)
        
        return {
            "text": result.text,
            "confidence": result.confidence,
            "language": result.language,
            "provider": result.provider,
            "word_count": len(result.text.split()),
            "character_count": len(result.text),
        }
    
    async def _load_image(self, image_path: str) -> np.ndarray:
        """Load image from file."""
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        return image
    
    async def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results."""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # Binarization (threshold)
        _, binary = cv2.threshold(
            enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        
        return binary
    
    async def _tesseract_ocr(self, image: np.ndarray) -> OCRResult:
        """Perform OCR using Tesseract."""
        # Convert numpy array to PIL Image
        pil_image = Image.fromarray(image)
        
        # Get OCR data with confidence
        ocr_data = pytesseract.image_to_data(
            pil_image, lang=self.language, output_type=pytesseract.Output.DICT
        )
        
        # Extract text and calculate average confidence
        text_parts = []
        confidences = []
        
        for i, word in enumerate(ocr_data["text"]):
            if word.strip():
                text_parts.append(word)
                conf = int(ocr_data["conf"][i])
                if conf > 0:
                    confidences.append(conf)
        
        text = " ".join(text_parts)
        avg_confidence = (
            sum(confidences) / len(confidences) / 100.0
            if confidences
            else 0.0
        )
        
        return OCRResult(
            text=text,
            confidence=avg_confidence,
            language=self.language,
            provider="tesseract",
        )
    
    async def _easyocr_ocr(self, image: np.ndarray) -> OCRResult:
        """Perform OCR using EasyOCR."""
        if self.easyocr_reader is None:
            raise RuntimeError("EasyOCR reader not initialized")
        
        # EasyOCR expects RGB, convert if needed
        if len(image.shape) == 2:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        else:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Perform OCR
        results = self.easyocr_reader.readtext(image_rgb)
        
        # Extract text and confidence
        text_parts = []
        confidences = []
        
        for (bbox, text, confidence) in results:
            text_parts.append(text)
            confidences.append(confidence)
        
        text = " ".join(text_parts)
        avg_confidence = (
            sum(confidences) / len(confidences) if confidences else 0.0
        )
        
        return OCRResult(
            text=text,
            confidence=avg_confidence,
            language=self.language,
            provider="easyocr",
        )
