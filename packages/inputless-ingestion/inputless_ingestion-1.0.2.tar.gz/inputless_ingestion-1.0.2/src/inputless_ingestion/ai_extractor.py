"""
AI-powered knowledge extractor using Large Language Models.

Supports OpenAI GPT-4 and Anthropic Claude for structured knowledge extraction.
"""

from typing import Dict, Any, List, Optional
from openai import OpenAI
from anthropic import Anthropic
import json
import re

from .models import KnowledgeExtraction
from .exceptions import NLPProcessingError


class AIKnowledgeExtractor:
    """
    AI-powered knowledge extractor using LLMs.
    
    Supports OpenAI GPT-4 and Anthropic Claude for structured
    knowledge extraction and document analysis.
    """
    
    def __init__(
        self,
        llm_provider: str = "openai",
        model: str = "gpt-4",
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ):
        """
        Initialize AI extractor.
        
        Args:
            llm_provider: LLM provider ('openai' or 'anthropic')
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
        """
        self.llm_provider = llm_provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize LLM client
        if llm_provider == "openai":
            self.client = OpenAI()
        elif llm_provider == "anthropic":
            self.client = Anthropic()
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")
    
    async def extract_knowledge(
        self, text: str, document_type: Optional[str] = None
    ) -> KnowledgeExtraction:
        """
        Extract structured knowledge from text.
        
        Args:
            text: Input text
            document_type: Type of document (optional)
            
        Returns:
            KnowledgeExtraction with extracted information
            
        Raises:
            NLPProcessingError: If knowledge extraction fails
        """
        try:
            prompt = self._build_extraction_prompt(text, document_type)
            
            response = await self._call_llm(prompt)
            
            # Parse JSON response
            try:
                knowledge_dict = json.loads(response)
            except json.JSONDecodeError:
                # Fallback: try to extract JSON from markdown code blocks
                knowledge_dict = self._extract_json_from_markdown(response)
            
            return KnowledgeExtraction(**knowledge_dict)
        except Exception as e:
            raise NLPProcessingError(f"Knowledge extraction failed: {str(e)}") from e
    
    async def summarize(
        self, text: str, max_length: int = 200
    ) -> str:
        """
        Generate document summary.
        
        Args:
            text: Input text
            max_length: Maximum summary length
            
        Returns:
            Summary text
        """
        prompt = f"""Summarize the following document in {max_length} words or less:

{text}

Summary:"""
        
        response = await self._call_llm(prompt)
        return response.strip()
    
    async def extract_insights(self, text: str) -> List[str]:
        """
        Extract business insights from text.
        
        Args:
            text: Input text
            
        Returns:
            List of insights
        """
        prompt = f"""Extract key business insights from the following document. Return as a JSON array of insight strings:

{text}

Insights (JSON array):"""
        
        response = await self._call_llm(prompt)
        
        try:
            insights = json.loads(response)
            return insights if isinstance(insights, list) else [insights]
        except json.JSONDecodeError:
            # Fallback: return as single insight
            return [response.strip()]
    
    def _build_extraction_prompt(
        self, text: str, document_type: Optional[str]
    ) -> str:
        """Build prompt for knowledge extraction."""
        doc_type_context = (
            f"This is a {document_type} document. "
            if document_type
            else ""
        )
        
        prompt = f"""Extract structured knowledge from the following {doc_type_context}document. Return a JSON object with the following structure:
{{
    "summary": "Brief summary of the document",
    "entities": [{{"name": "...", "type": "...", "description": "..."}}],
    "relationships": [{{"entity1": "...", "entity2": "...", "relationship": "..."}}],
    "insights": ["insight1", "insight2", ...],
    "key_points": ["point1", "point2", ...]
}}

Document:
{text}

Extracted Knowledge (JSON):"""
        
        return prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API (synchronous calls wrapped in async)."""
        import asyncio
        
        # Run synchronous LLM calls in executor to avoid blocking
        loop = asyncio.get_event_loop()
        
        if self.llm_provider == "openai":
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
            )
            return response.choices[0].message.content
        elif self.llm_provider == "anthropic":
            response = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[{"role": "user", "content": prompt}],
                )
            )
            return response.content[0].text
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    
    def _extract_json_from_markdown(self, text: str) -> Dict[str, Any]:
        """Extract JSON from markdown code blocks."""
        # Try to find JSON in code blocks
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # Try to find JSON object directly
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        
        # Fallback: return empty structure
        return {
            "summary": text[:200],
            "entities": [],
            "relationships": [],
            "insights": [],
            "key_points": [],
        }
