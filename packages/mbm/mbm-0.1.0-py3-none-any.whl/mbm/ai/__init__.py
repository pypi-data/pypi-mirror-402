"""
MBM AI Module

Local NLP-powered AI assistant using spaCy for intent detection
and entity extraction. No cloud LLMs - privacy first.
"""

from mbm.ai.assistant import AIAssistant
from mbm.ai.nlp import NLPProcessor, Intent, EntityType
from mbm.ai.response import AIResponse

__all__ = [
    "AIAssistant",
    "NLPProcessor",
    "Intent",
    "EntityType",
    "AIResponse",
]
