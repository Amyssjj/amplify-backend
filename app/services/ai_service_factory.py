"""
Factory for creating AI story enhancement services.
"""
import logging
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.services.ai_service_interface import AIStoryEnhancementService
from app.services.gemini_service import GeminiService
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Custom exception for AI service factory errors."""
    pass


class AIServiceFactory:
    """Factory for creating and managing AI story enhancement services."""

    def __init__(self, enable_fallback: bool = True):
        """
        Initialize AI service factory.

        Args:
            enable_fallback: Whether to enable fallback to secondary providers
        """
        self.enable_fallback = enable_fallback
        self._service_cache: Optional[AIStoryEnhancementService] = None

    def create_service(self) -> AIStoryEnhancementService:
        """
        Create an AI service based on configuration.

        Returns:
            AIStoryEnhancementService instance

        Raises:
            AIServiceError: If service creation fails
        """
        # Return cached service if available
        if self._service_cache:
            return self._service_cache

        primary_provider = settings.ai_provider

        try:
            # Try to create primary service
            service = self._create_service_for_provider(primary_provider)
            self._service_cache = service
            logger.info(f"✅ Created {primary_provider} AI service successfully")
            return service

        except Exception as e:
            logger.warning(f"⚠️ Failed to create {primary_provider} service: {str(e)}")

            if not self.enable_fallback:
                raise AIServiceError(f"Failed to create {primary_provider} service: {str(e)}")

            # Try fallback providers
            available_providers = self.get_available_providers()
            fallback_providers = [p for p in available_providers if p != primary_provider]

            for provider in fallback_providers:
                try:
                    logger.info(f"🔄 Attempting fallback to {provider} service")
                    service = self._create_service_for_provider(provider)
                    self._service_cache = service
                    logger.info(f"✅ Fallback to {provider} AI service successful")
                    return service
                except Exception as fallback_error:
                    logger.warning(f"⚠️ Fallback to {provider} also failed: {str(fallback_error)}")
                    continue

            # If all providers failed
            raise AIServiceError(f"Failed to create any AI service. Primary: {str(e)}")

    def _create_service_for_provider(self, provider: str) -> AIStoryEnhancementService:
        """
        Create service for specific provider.

        Args:
            provider: The AI provider name

        Returns:
            AIStoryEnhancementService instance

        Raises:
            AIServiceError: If provider is unsupported or creation fails
        """
        if provider == "gemini":
            return self._create_gemini_service()
        elif provider == "openai":
            return self._create_openai_service()
        else:
            raise AIServiceError(f"Unsupported AI provider: {provider}")

    def _create_gemini_service(self) -> GeminiService:
        """Create Gemini service with validation."""
        if not settings.gemini_api_key:
            raise AIServiceError("Gemini API key is required but not provided")

        return GeminiService(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model
        )

    def _create_openai_service(self) -> OpenAIService:
        """Create OpenAI service with validation."""
        if not settings.openai_api_key:
            raise AIServiceError("OpenAI API key is required but not provided")

        return OpenAIService(
            api_key=settings.openai_api_key,
            model=settings.openai_model
        )

    def get_available_providers(self) -> List[str]:
        """
        Get list of available AI providers based on API key availability.

        Returns:
            List of available provider names
        """
        available = []

        if settings.gemini_api_key:
            available.append("gemini")

        if settings.openai_api_key:
            available.append("openai")

        return available

    def get_provider_capabilities(self, provider: str) -> Dict[str, Any]:
        """
        Get capabilities information for a specific provider.

        Args:
            provider: The AI provider name

        Returns:
            Dictionary containing provider capabilities

        Raises:
            AIServiceError: If provider is unknown
        """
        if provider == "gemini":
            return {
                "name": "gemini",
                "supports_vision": True,
                "model": settings.gemini_model,
                "description": "Google Gemini AI with vision capabilities"
            }
        elif provider == "openai":
            vision_models = {"gpt-4-vision-preview", "gpt-4-turbo"}
            supports_vision = settings.openai_model in vision_models
            return {
                "name": "openai",
                "supports_vision": supports_vision,
                "model": settings.openai_model,
                "description": f"OpenAI GPT model{' with vision' if supports_vision else ''}"
            }
        else:
            raise AIServiceError(f"Unknown provider: {provider}")

    def clear_cache(self):
        """Clear the cached service instance."""
        self._service_cache = None
        logger.info("🗑️ AI service cache cleared")

    def get_current_provider(self) -> Optional[str]:
        """
        Get the name of the currently active provider.

        Returns:
            Provider name if service is cached, None otherwise
        """
        if self._service_cache:
            return self._service_cache.get_provider_name()
        return None

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on available AI services.

        Returns:
            Dictionary containing health status for each provider
        """
        health_status = {}
        available_providers = self.get_available_providers()

        for provider in available_providers:
            try:
                # Try to create service (but don't cache it)
                service = self._create_service_for_provider(provider)
                capabilities = self.get_provider_capabilities(provider)

                health_status[provider] = {
                    "status": "healthy",
                    "capabilities": capabilities,
                    "error": None
                }

            except Exception as e:
                health_status[provider] = {
                    "status": "unhealthy",
                    "capabilities": None,
                    "error": str(e)
                }

        return health_status


# Global factory instance
ai_service_factory = AIServiceFactory()
