"""
Unit tests for Gemini service interface implementation.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.gemini_service import GeminiService
from app.services.ai_service_interface import AIStoryEnhancementService


@pytest.mark.unit
class TestGeminiServiceInterface:
    """Test that GeminiService properly implements AIStoryEnhancementService interface."""

    def test_gemini_service_implements_interface(self):
        """Test that GeminiService implements AIStoryEnhancementService interface."""
        with patch('app.services.gemini_service.genai'), \
             patch('app.services.gemini_service.prompt_manager'):
            service = GeminiService(api_key="test_key")
            assert isinstance(service, AIStoryEnhancementService)

    def test_gemini_service_supports_vision(self):
        """Test that GeminiService supports vision capabilities."""
        with patch('app.services.gemini_service.genai'), \
             patch('app.services.gemini_service.prompt_manager'):
            service = GeminiService(api_key="test_key")
            assert service.supports_vision() is True

    def test_gemini_service_provider_name(self):
        """Test that GeminiService returns correct provider name."""
        with patch('app.services.gemini_service.genai'), \
             patch('app.services.gemini_service.prompt_manager'):
            service = GeminiService(api_key="test_key")
            assert service.get_provider_name() == "gemini"

    def test_gemini_service_has_existing_method(self):
        """Test that existing enhance_story_with_photo method is preserved."""
        with patch('app.services.gemini_service.genai'), \
             patch('app.services.gemini_service.prompt_manager'):
            service = GeminiService(api_key="test_key")

            # Method should exist and be callable
            assert hasattr(service, 'enhance_story_with_photo')
            assert callable(getattr(service, 'enhance_story_with_photo'))

    async def test_gemini_service_method_signature_compatible(self):
        """Test that method signature is compatible with interface."""
        with patch('app.services.gemini_service.genai'), \
             patch('app.services.gemini_service.prompt_manager'):
            service = GeminiService(api_key="test_key")

            # Mock the actual API call to avoid real requests
            with patch.object(service, '_call_gemini_api', new_callable=AsyncMock) as mock_api:
                mock_api.return_value = {
                    "enhanced_transcript": "Enhanced story",
                    "insights": {"test": "insight"}
                }

                # Should be able to call with interface signature
                result = await service.enhance_story_with_photo(
                    photo_base64="test_base64",
                    transcript="test story",
                    language="en"
                )

                # Should return expected type
                from app.services.gemini_service import GeminiResponse
                assert isinstance(result, GeminiResponse)
