"""
AI Response Model

Data models for AI assistant responses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from mbm.ai.nlp import Intent


@dataclass
class AIResponse:
    """
    Response from the AI assistant.
    
    Contains the result of processing a user query, including
    the detected intent, response text, and any media.
    """
    
    success: bool
    intent: Intent
    
    # Response content
    title: Optional[str] = None
    text: Optional[str] = None
    message: Optional[str] = None
    
    # Media (if applicable)
    media_path: Optional[str] = None
    media_type: Optional[str] = None  # "image", "video", etc.
    media_url: Optional[str] = None
    
    # Metadata
    source: Optional[str] = None
    query: Optional[str] = None
    confidence: float = 1.0
    
    @classmethod
    def success_info(
        cls,
        title: str,
        text: str,
        source: Optional[str] = None,
        query: Optional[str] = None,
    ) -> AIResponse:
        """Create a successful info response."""
        return cls(
            success=True,
            intent=Intent.INFO,
            title=title,
            text=text,
            source=source,
            query=query,
        )
    
    @classmethod
    def success_image(
        cls,
        media_path: str,
        media_url: Optional[str] = None,
        message: Optional[str] = None,
        source: Optional[str] = None,
    ) -> AIResponse:
        """Create a successful image response."""
        return cls(
            success=True,
            intent=Intent.IMAGE,
            media_path=media_path,
            media_type="image",
            media_url=media_url,
            message=message,
            source=source,
        )
    
    @classmethod
    def error(cls, message: str, intent: Intent = Intent.UNKNOWN) -> AIResponse:
        """Create an error response."""
        return cls(
            success=False,
            intent=intent,
            message=message,
        )
    
    @classmethod
    def greeting(cls, message: str) -> AIResponse:
        """Create a greeting response."""
        return cls(
            success=True,
            intent=Intent.GREETING,
            text=message,
        )
    
    @classmethod
    def help_response(cls, text: str) -> AIResponse:
        """Create a help response."""
        return cls(
            success=True,
            intent=Intent.HELP,
            title="Help",
            text=text,
        )
