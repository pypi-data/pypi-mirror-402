"""
NLP processor for extracting entities, topics, and insights from text.

Supports entity recognition, topic modeling, sentiment analysis, and keyword extraction.
"""

from typing import Dict, Any, List, Optional
import spacy
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from textblob import TextBlob

from .models import Entity, Topic
from .exceptions import NLPProcessingError


class NLPProcessor:
    """
    NLP processor for entity recognition, topic modeling, and sentiment analysis.

    Uses spaCy for NER, scikit-learn for topic modeling, and TextBlob for sentiment.
    """

    def __init__(
        self,
        model: str = "en_core_web_sm",
        max_entities: int = 100,
        num_topics: int = 5,
    ):
        """
        Initialize NLP processor.

        Args:
            model: spaCy model name
            max_entities: Maximum entities to extract
            num_topics: Number of topics for topic modeling
        """
        self.model = model
        self.max_entities = max_entities
        self.num_topics = num_topics

        # Load spaCy model
        try:
            self.nlp = spacy.load(model)
        except OSError:
            raise ValueError(
                f"spaCy model '{model}' not found. "
                f"Install with: python -m spacy download {model}"
            )

        # Initialize stopwords with better error handling
        self.stopwords = set()
        try:
            self.stopwords = set(stopwords.words("english"))
        except (LookupError, OSError, AttributeError):
            # Try to download NLTK data if missing
            try:
                import nltk

                nltk.download("stopwords", quiet=True)
                nltk.download("punkt", quiet=True)
                self.stopwords = set(stopwords.words("english"))
            except Exception:
                # Fallback to empty set if download fails
                # This allows the processor to work without NLTK stopwords
                self.stopwords = set()

    async def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract named entities from text.

        Args:
            text: Input text

        Returns:
            List of extracted entities

        Raises:
            NLPProcessingError: If entity extraction fails
        """
        try:
            doc = self.nlp(text)

            entities = []
            for ent in doc.ents:
                entities.append(
                    Entity(
                        text=ent.text,
                        label=ent.label_,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=1.0,  # spaCy doesn't provide confidence by default
                    )
                )

            # Limit to max_entities
            return entities[: self.max_entities]
        except Exception as e:
            raise NLPProcessingError(f"Entity extraction failed: {str(e)}") from e

    async def extract_topics(
        self, text: str, num_topics: Optional[int] = None
    ) -> List[Topic]:
        """
        Extract topics from text using LDA.

        Args:
            text: Input text
            num_topics: Number of topics (default: self.num_topics)

        Returns:
            List of topics with keywords

        Raises:
            NLPProcessingError: If topic extraction fails
        """
        try:
            num_topics = num_topics or self.num_topics

            # Tokenize and preprocess
            sentences = sent_tokenize(text)

            if len(sentences) < 2:
                # Not enough sentences for topic modeling
                return []

            # Vectorize
            vectorizer = TfidfVectorizer(
                max_features=100, stop_words="english", ngram_range=(1, 2)
            )
            X = vectorizer.fit_transform(sentences)

            # Topic modeling
            lda = LatentDirichletAllocation(n_components=num_topics, random_state=42)
            lda.fit(X)

            # Extract topics
            topics = []
            feature_names = vectorizer.get_feature_names_out()

            for topic_idx, topic in enumerate(lda.components_):
                top_keywords_idx = topic.argsort()[-10:][::-1]
                keywords = [feature_names[i] for i in top_keywords_idx]
                weight = topic.sum() / lda.components_.sum()

                topics.append(
                    Topic(
                        topic_id=topic_idx,
                        keywords=keywords,
                        weight=float(weight),
                    )
                )

            return topics
        except Exception as e:
            raise NLPProcessingError(f"Topic extraction failed: {str(e)}") from e

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text.

        Args:
            text: Input text

        Returns:
            Sentiment analysis result

        Raises:
            NLPProcessingError: If sentiment analysis fails
        """
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            # Classify sentiment
            if polarity > 0.1:
                sentiment = "positive"
            elif polarity < -0.1:
                sentiment = "negative"
            else:
                sentiment = "neutral"

            return {
                "sentiment": sentiment,
                "polarity": float(polarity),
                "subjectivity": float(subjectivity),
            }
        except Exception as e:
            raise NLPProcessingError(f"Sentiment analysis failed: {str(e)}") from e

    async def extract_keywords(self, text: str, num_keywords: int = 10) -> List[str]:
        """
        Extract keywords using TF-IDF.

        Args:
            text: Input text
            num_keywords: Number of keywords to extract

        Returns:
            List of keywords

        Raises:
            NLPProcessingError: If keyword extraction fails
        """
        try:
            # Tokenize
            tokens = word_tokenize(text.lower())
            tokens = [t for t in tokens if t.isalnum() and t not in self.stopwords]

            if not tokens:
                return []

            # Vectorize
            vectorizer = TfidfVectorizer(max_features=num_keywords)
            X = vectorizer.fit_transform([" ".join(tokens)])

            # Get feature names
            feature_names = vectorizer.get_feature_names_out()

            # Get scores
            scores = X.toarray()[0]

            # Sort by score
            keyword_scores = list(zip(feature_names, scores))
            keyword_scores.sort(key=lambda x: x[1], reverse=True)

            return [kw for kw, _ in keyword_scores]
        except Exception as e:
            raise NLPProcessingError(f"Keyword extraction failed: {str(e)}") from e

    async def classify_text(self, text: str) -> Dict[str, Any]:
        """
        Classify document type.

        Args:
            text: Input text

        Returns:
            Classification result
        """
        # Simple rule-based classification
        # In production, use a trained classifier

        text_lower = text.lower()

        if any(word in text_lower for word in ["contract", "agreement", "terms"]):
            doc_type = "legal"
        elif any(word in text_lower for word in ["invoice", "payment", "bill"]):
            doc_type = "financial"
        elif any(word in text_lower for word in ["report", "analysis", "summary"]):
            doc_type = "report"
        else:
            doc_type = "general"

        return {
            "document_type": doc_type,
            "confidence": 0.7,  # Placeholder
        }
