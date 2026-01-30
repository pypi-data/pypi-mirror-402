"""
NLP Processor

Local NLP processing using spaCy for intent detection, entity extraction,
and query cleanup. Falls back to keyword matching if spaCy is unavailable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any

from mbm.core.constants import SPACY_MODEL


class Intent(str, Enum):
    """Detected user intents."""
    
    IMAGE = "image"
    INFO = "info"
    GREETING = "greeting"
    HELP = "help"
    UNKNOWN = "unknown"


class EntityType(str, Enum):
    """Types of extracted entities."""
    
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    TOPIC = "topic"
    UNKNOWN = "unknown"


@dataclass
class Entity:
    """Represents an extracted entity."""
    
    text: str
    type: EntityType
    confidence: float = 1.0
    
    def __str__(self) -> str:
        return f"{self.text} ({self.type.value})"


@dataclass
class NLPResult:
    """Result of NLP processing."""
    
    intent: Intent
    entities: list[Entity] = field(default_factory=list)
    cleaned_query: str = ""
    confidence: float = 1.0
    raw_input: str = ""
    
    @property
    def primary_entity(self) -> Optional[Entity]:
        """Get the most important entity."""
        if self.entities:
            return self.entities[0]
        return None
    
    @property
    def search_query(self) -> str:
        """Get a clean search query based on entities."""
        if self.entities:
            return " ".join(e.text for e in self.entities)
        return self.cleaned_query


class NLPProcessor:
    """
    Natural Language Processor using spaCy.
    
    Handles intent detection, entity extraction, and query cleanup
    using local models only - no cloud services.
    """
    
    # Keywords for intent detection (fallback mode)
    IMAGE_KEYWORDS = {
        "show", "image", "picture", "photo", "pic", "display",
        "view", "see", "look", "visual", "photograph"
    }
    
    INFO_KEYWORDS = {
        "what", "who", "where", "when", "why", "how", "tell",
        "explain", "describe", "info", "information", "about",
        "define", "meaning", "is"
    }
    
    GREETING_KEYWORDS = {
        "hello", "hi", "hey", "greetings", "good morning",
        "good afternoon", "good evening", "howdy"
    }
    
    HELP_KEYWORDS = {
        "help", "commands", "usage", "how to", "guide"
    }
    
    def __init__(self, use_spacy: bool = True):
        """
        Initialize the NLP processor.
        
        Args:
            use_spacy: Whether to use spaCy (will fallback if unavailable)
        """
        self.use_spacy = use_spacy
        self._nlp: Optional[Any] = None
        
        if use_spacy:
            self._load_spacy()
    
    def _load_spacy(self) -> bool:
        """
        Load spaCy model.
        
        Returns:
            True if loaded successfully
        """
        try:
            import spacy
            self._nlp = spacy.load(SPACY_MODEL)
            return True
        except (ImportError, OSError):
            # spaCy not available or model not downloaded
            self._nlp = None
            self.use_spacy = False
            return False
    
    def process(self, text: str) -> NLPResult:
        """
        Process user input to extract intent and entities.
        
        Args:
            text: User's natural language input
            
        Returns:
            NLPResult with intent and entities
        """
        # Clean input
        cleaned = self._clean_text(text)
        
        if self._nlp is not None:
            return self._process_with_spacy(text, cleaned)
        else:
            return self._process_with_keywords(text, cleaned)
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize user input.
        
        Args:
            text: Raw user input
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Remove special characters but keep letters, numbers, spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalize whitespace again
        text = " ".join(text.split())
        
        return text.strip()
    
    def _process_with_spacy(self, raw: str, cleaned: str) -> NLPResult:
        """
        Process text using spaCy NLP.
        
        Args:
            raw: Original input
            cleaned: Cleaned input
            
        Returns:
            NLPResult
        """
        doc = self._nlp(cleaned)
        
        # Extract entities
        entities = []
        for ent in doc.ents:
            entity_type = self._map_spacy_entity(ent.label_)
            entities.append(Entity(
                text=ent.text,
                type=entity_type,
                confidence=0.9,
            ))
        
        # If no named entities, extract noun chunks as topics
        if not entities:
            for chunk in doc.noun_chunks:
                # Filter out common words
                if chunk.root.pos_ in ('NOUN', 'PROPN'):
                    entities.append(Entity(
                        text=chunk.text,
                        type=EntityType.TOPIC,
                        confidence=0.7,
                    ))
        
        # Detect intent
        intent = self._detect_intent_with_spacy(doc, raw.lower())
        
        return NLPResult(
            intent=intent,
            entities=entities,
            cleaned_query=cleaned,
            confidence=0.85,
            raw_input=raw,
        )
    
    def _map_spacy_entity(self, label: str) -> EntityType:
        """Map spaCy entity label to our EntityType."""
        mapping = {
            'PERSON': EntityType.PERSON,
            'ORG': EntityType.ORGANIZATION,
            'GPE': EntityType.LOCATION,
            'LOC': EntityType.LOCATION,
            'FAC': EntityType.LOCATION,
        }
        return mapping.get(label, EntityType.TOPIC)
    
    def _detect_intent_with_spacy(self, doc: Any, lower_text: str) -> Intent:
        """Detect intent using spaCy analysis and keywords."""
        
        # Check for image keywords
        if any(kw in lower_text for kw in self.IMAGE_KEYWORDS):
            return Intent.IMAGE
        
        # Check for greeting
        if any(kw in lower_text for kw in self.GREETING_KEYWORDS):
            return Intent.GREETING
        
        # Check for help
        if any(kw in lower_text for kw in self.HELP_KEYWORDS):
            return Intent.HELP
        
        # Check for info keywords or question structure
        if any(kw in lower_text for kw in self.INFO_KEYWORDS):
            return Intent.INFO
        
        # Check if it's a question (ends with ?)
        if doc.text.strip().endswith('?'):
            return Intent.INFO
        
        # Default to info for most queries
        return Intent.INFO
    
    def _process_with_keywords(self, raw: str, cleaned: str) -> NLPResult:
        """
        Process text using keyword matching (fallback mode).
        
        Args:
            raw: Original input
            cleaned: Cleaned input
            
        Returns:
            NLPResult
        """
        lower = cleaned.lower()
        words = lower.split()
        
        # Detect intent (order matters - check most specific first)
        intent = Intent.UNKNOWN
        
        # Check for help first (most specific)
        if any(kw in lower for kw in self.HELP_KEYWORDS):
            intent = Intent.HELP
        elif any(kw in lower for kw in self.GREETING_KEYWORDS):
            intent = Intent.GREETING
        elif any(kw in lower for kw in self.IMAGE_KEYWORDS):
            intent = Intent.IMAGE
        elif any(kw in lower for kw in self.INFO_KEYWORDS):
            intent = Intent.INFO
        else:
            intent = Intent.INFO  # Default
        
        # Extract entities (simple: remove common words)
        stopwords = {
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
            'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
            'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'under', 'again', 'further', 'then', 'once',
            'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
            'you', 'your', 'yours', 'yourself', 'yourselves', 'he',
            'him', 'his', 'himself', 'she', 'her', 'hers', 'herself',
            'it', 'its', 'itself', 'they', 'them', 'their', 'theirs',
            'themselves', 'what', 'which', 'who', 'whom', 'this',
            'that', 'these', 'those', 'am', 'show', 'tell', 'about',
            'image', 'picture', 'photo', 'info', 'information',
        }
        
        # Extract meaningful words
        meaningful_words = [w for w in words if w not in stopwords and len(w) > 2]
        
        entities = []
        if meaningful_words:
            # Combine as a single topic entity
            topic_text = " ".join(meaningful_words)
            entities.append(Entity(
                text=topic_text.title(),
                type=EntityType.TOPIC,
                confidence=0.6,
            ))
        
        return NLPResult(
            intent=intent,
            entities=entities,
            cleaned_query=cleaned,
            confidence=0.6,
            raw_input=raw,
        )
    
    def extract_search_query(self, text: str) -> str:
        """
        Extract a clean search query from user input.
        
        Args:
            text: User input
            
        Returns:
            Clean search query string
        """
        result = self.process(text)
        return result.search_query
