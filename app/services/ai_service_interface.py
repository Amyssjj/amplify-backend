"""
Abstract interface for AI story enhancement services.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from app.schemas.ai_response import AIResponse


class AIStoryEnhancementService(ABC):
    """Abstract base class for AI story enhancement services."""

    @abstractmethod
    async def enhance_story_with_photo(
        self,
        photo_base64: str,
        transcript: str,
        language: str = "en"
    ) -> AIResponse:
        """
        Enhance a story transcript using photo analysis.

        Args:
            photo_base64: Base64 encoded image data
            transcript: Original story transcript
            language: Language code (ISO 639-1)

        Returns:
            AIResponse with enhanced transcript and insights

        Raises:
            GeminiError: If enhancement fails
        """
        pass

    @abstractmethod
    def supports_vision(self) -> bool:
        """
        Check if this service supports vision/image analysis.

        Returns:
            True if service can analyze images, False otherwise
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of the AI provider.

        Returns:
            String identifier for the AI provider (e.g., "gemini", "openai")
        """
        pass
