"""
Tests for the AI/NLP module.
"""

import pytest

from mbm.ai.nlp import NLPProcessor, Intent, EntityType


class TestNLPProcessor:
    """Tests for NLP processing."""
    
    def test_intent_detection_image(self):
        nlp = NLPProcessor(use_spacy=False)  # Use keyword fallback
        
        result = nlp.process("show me an image of cats")
        assert result.intent == Intent.IMAGE
        
        result = nlp.process("picture of mountains")
        assert result.intent == Intent.IMAGE
    
    def test_intent_detection_info(self):
        nlp = NLPProcessor(use_spacy=False)
        
        result = nlp.process("what is Python programming")
        assert result.intent == Intent.INFO
        
        result = nlp.process("tell me about MBM University")
        assert result.intent == Intent.INFO
    
    def test_intent_detection_greeting(self):
        nlp = NLPProcessor(use_spacy=False)
        
        result = nlp.process("hello")
        assert result.intent == Intent.GREETING
        
        result = nlp.process("hi there")
        assert result.intent == Intent.GREETING
    
    def test_intent_detection_help(self):
        nlp = NLPProcessor(use_spacy=False)
        
        result = nlp.process("help me")
        assert result.intent == Intent.HELP
        
        result = nlp.process("show commands")
        assert result.intent == Intent.HELP
    
    def test_entity_extraction(self):
        nlp = NLPProcessor(use_spacy=False)
        
        result = nlp.process("what is Python programming")
        assert len(result.entities) > 0
        assert "python" in result.search_query.lower()
    
    def test_query_cleanup(self):
        nlp = NLPProcessor(use_spacy=False)
        
        # Test with messy input
        result = nlp.process("   what   is  MBM??  ")
        assert result.cleaned_query  # Should be cleaned
    
    def test_extract_search_query(self):
        nlp = NLPProcessor(use_spacy=False)
        
        query = nlp.extract_search_query("show me image of Taj Mahal")
        assert "taj" in query.lower() or "mahal" in query.lower()


class TestAIResponse:
    """Tests for AI response models."""
    
    def test_success_info_response(self):
        from mbm.ai.response import AIResponse
        
        response = AIResponse.success_info(
            title="Test",
            text="Test content",
            source="Wikipedia"
        )
        
        assert response.success is True
        assert response.intent == Intent.INFO
        assert response.title == "Test"
        assert response.source == "Wikipedia"
    
    def test_error_response(self):
        from mbm.ai.response import AIResponse
        
        response = AIResponse.error("Something went wrong")
        
        assert response.success is False
        assert response.message == "Something went wrong"
    
    def test_greeting_response(self):
        from mbm.ai.response import AIResponse
        
        response = AIResponse.greeting("Hello!")
        
        assert response.success is True
        assert response.intent == Intent.GREETING
        assert response.text == "Hello!"
