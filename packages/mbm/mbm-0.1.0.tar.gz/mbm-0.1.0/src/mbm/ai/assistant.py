"""
AI Assistant

Main AI assistant class that orchestrates NLP processing,
information retrieval, and media handling.
"""

from __future__ import annotations

import random
from typing import Optional

from mbm.ai.nlp import NLPProcessor, Intent, NLPResult
from mbm.ai.response import AIResponse
from mbm.services.wikipedia import WikipediaService
from mbm.services.wikimedia import WikimediaService
from mbm.utils.media import MediaHandler


class AIAssistant:
    """
    MBM AI Assistant.
    
    Processes natural language queries using local NLP (spaCy),
    fetches information from legal public sources (Wikipedia),
    and handles media display.
    
    Design principles:
    - Privacy first: No cloud LLMs
    - Legal only: Public APIs and Wikimedia Commons
    - Fast: Local processing where possible
    - Ethical: No scraping or private data access
    """
    
    GREETINGS = [
        "Hello! I'm the MBM AI Assistant. How can I help you?",
        "Hi there! Ask me anything about general knowledge.",
        "Greetings! I can help you find information or show images.",
        "Hey! Ready to assist. What would you like to know?",
    ]
    
    def __init__(self, use_nlp: bool = True):
        """
        Initialize the AI assistant.
        
        Args:
            use_nlp: Whether to use spaCy NLP (falls back to keywords)
        """
        self.nlp = NLPProcessor(use_spacy=use_nlp)
        self.wikipedia = WikipediaService()
        self.wikimedia = WikimediaService()
        self.media_handler = MediaHandler()
    
    def process_query(self, query: str) -> AIResponse:
        """
        Process a user query and return an appropriate response.
        
        Args:
            query: Natural language query from user
            
        Returns:
            AIResponse with result or error
        """
        if not query or not query.strip():
            return AIResponse.error("Please enter a query.")
        
        # Process with NLP
        nlp_result = self.nlp.process(query)
        
        # Route based on intent
        if nlp_result.intent == Intent.GREETING:
            return self._handle_greeting()
        
        elif nlp_result.intent == Intent.HELP:
            return self._handle_help()
        
        elif nlp_result.intent == Intent.IMAGE:
            return self._handle_image_request(nlp_result)
        
        elif nlp_result.intent == Intent.INFO:
            return self._handle_info_request(nlp_result)
        
        else:
            # Default to info request
            return self._handle_info_request(nlp_result)
    
    def _handle_greeting(self) -> AIResponse:
        """Handle greeting intent."""
        return AIResponse.greeting(random.choice(self.GREETINGS))
    
    def _handle_help(self) -> AIResponse:
        """Handle help intent."""
        help_text = """
## MBM AI Assistant Help

### What I Can Do
- **Answer questions**: Ask me about any topic
- **Show images**: Say "show image of [topic]"
- **General knowledge**: I use Wikipedia for information

### Example Queries
- "What is MBM University?"
- "Show image of Jodhpur"
- "Tell me about Python programming"
- "Who is Albert Einstein?"

### Privacy
- I use local NLP (no cloud AI)
- Images from Wikimedia Commons only
- No tracking or data collection

### Tips
- Be specific in your queries
- Use "show image" for visual content
- Use "what is" or "tell me about" for info
"""
        return AIResponse.help_response(help_text)
    
    def _handle_image_request(self, nlp_result: NLPResult) -> AIResponse:
        """
        Handle image search request.
        
        Args:
            nlp_result: NLP processing result
            
        Returns:
            AIResponse with image or error
        """
        search_query = nlp_result.search_query
        
        if not search_query:
            return AIResponse.error(
                "I couldn't understand what image you're looking for. "
                "Try: 'show image of [topic]'"
            )
        
        try:
            # Search Wikimedia Commons for image
            image_url = self.wikimedia.search_image(search_query)
            
            if not image_url:
                return AIResponse.error(
                    f"No images found for '{search_query}' on Wikimedia Commons."
                )
            
            # Download to temp file and open
            temp_path = self.media_handler.download_and_open(image_url)
            
            if temp_path:
                return AIResponse.success_image(
                    media_path=temp_path,
                    media_url=image_url,
                    message=f"Showing image for: {search_query}",
                    source="Wikimedia Commons",
                )
            else:
                return AIResponse.error(
                    "Failed to download or display the image."
                )
                
        except Exception as e:
            return AIResponse.error(f"Image request failed: {str(e)}")
    
    def _handle_info_request(self, nlp_result: NLPResult) -> AIResponse:
        """
        Handle information request.
        
        Args:
            nlp_result: NLP processing result
            
        Returns:
            AIResponse with information or error
        """
        search_query = nlp_result.search_query
        
        if not search_query:
            return AIResponse.error(
                "I couldn't understand your question. "
                "Try: 'What is [topic]?' or 'Tell me about [topic]'"
            )
        
        try:
            # Fetch from Wikipedia
            result = self.wikipedia.get_summary(search_query)
            
            if result:
                return AIResponse.success_info(
                    title=result.get("title", search_query),
                    text=result.get("extract", "No information available."),
                    source="Wikipedia",
                    query=search_query,
                )
            else:
                return AIResponse.error(
                    f"No information found for '{search_query}'. "
                    "Try a different search term."
                )
                
        except Exception as e:
            return AIResponse.error(f"Information request failed: {str(e)}")
    
    def cleanup(self) -> None:
        """Clean up temporary files."""
        self.media_handler.cleanup()
