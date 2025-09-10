"""
Unit tests for AI service factory.
"""
import pytest
from unittest.mock import Mock, patch
from app.services.ai_service_factory import AIServiceFactory, AIServiceError
from app.services.ai_service_interface import AIStoryEnhancementService
from app.services.gemini_service import GeminiService
from app.services.openai_service import OpenAIService


@pytest.mark.unit
class TestAIServiceFactory:
    """Test AI service factory functionality."""

    def test_create_service_with_gemini_provider(self):
        """Test creating Gemini service when provider is set to gemini."""
        with patch('app.services.ai_service_factory.settings') as mock_settings, \
             patch('app.services.ai_service_factory.GeminiService') as mock_gemini:

            mock_settings.ai_provider = "gemini"
            mock_settings.gemini_api_key = "test_gemini_key"
            mock_settings.gemini_model = "models/gemini-2.5-flash-lite"

            mock_service = Mock(spec=AIStoryEnhancementService)
            mock_gemini.return_value = mock_service

            factory = AIServiceFactory()
            service = factory.create_service()

            assert service == mock_service
            mock_gemini.assert_called_once_with(
                api_key="test_gemini_key",
                model="models/gemini-2.5-flash-lite"
            )

    def test_create_service_with_openai_provider(self):
        """Test creating OpenAI service when provider is set to openai."""
        with patch('app.services.ai_service_factory.settings') as mock_settings, \
             patch('app.services.ai_service_factory.OpenAIService') as mock_openai:

            mock_settings.ai_provider = "openai"
            mock_settings.openai_api_key = "test_openai_key"
            mock_settings.openai_model = "gpt-4-vision-preview"

            mock_service = Mock(spec=AIStoryEnhancementService)
            mock_openai.return_value = mock_service

            factory = AIServiceFactory()
            service = factory.create_service()

            assert service == mock_service
            mock_openai.assert_called_once_with(
                api_key="test_openai_key",
                model="gpt-4-vision-preview"
            )

    def test_create_service_with_invalid_provider_raises_error(self):
        """Test that invalid provider raises error."""
        with patch('app.services.ai_service_factory.settings') as mock_settings:
            mock_settings.ai_provider = "invalid_provider"
            # No API keys available, so no fallback providers
            mock_settings.gemini_api_key = None
            mock_settings.openai_api_key = None

            factory = AIServiceFactory()

            with pytest.raises(AIServiceError, match="Failed to create any AI service"):
                factory.create_service()

    def test_create_service_with_fallback_when_primary_fails(self):
        """Test fallback to secondary provider when primary fails."""
        with patch('app.services.ai_service_factory.settings') as mock_settings, \
             patch('app.services.ai_service_factory.GeminiService') as mock_gemini, \
             patch('app.services.ai_service_factory.OpenAIService') as mock_openai:

            mock_settings.ai_provider = "gemini"
            mock_settings.gemini_api_key = "test_gemini_key"
            mock_settings.openai_api_key = "test_openai_key"
            mock_settings.openai_model = "gpt-4-vision-preview"

            # Primary service fails
            mock_gemini.side_effect = Exception("Gemini service unavailable")

            # Secondary service succeeds
            mock_service = Mock(spec=AIStoryEnhancementService)
            mock_openai.return_value = mock_service

            factory = AIServiceFactory(enable_fallback=True)
            service = factory.create_service()

            assert service == mock_service
            mock_openai.assert_called_once()

    def test_create_service_without_fallback_raises_error_when_primary_fails(self):
        """Test that without fallback, primary failure raises error."""
        with patch('app.services.ai_service_factory.settings') as mock_settings, \
             patch('app.services.ai_service_factory.GeminiService') as mock_gemini:

            mock_settings.ai_provider = "gemini"
            mock_settings.gemini_api_key = "test_gemini_key"

            mock_gemini.side_effect = Exception("Gemini service unavailable")

            factory = AIServiceFactory(enable_fallback=False)

            with pytest.raises(AIServiceError, match="Failed to create"):
                factory.create_service()

    def test_create_service_validates_api_keys_before_creation(self):
        """Test that API keys are validated before service creation."""
        with patch('app.services.ai_service_factory.settings') as mock_settings:
            mock_settings.ai_provider = "gemini"
            mock_settings.gemini_api_key = None  # No API key
            mock_settings.openai_api_key = None  # No fallback either

            factory = AIServiceFactory()

            with pytest.raises(AIServiceError, match="Failed to create any AI service"):
                factory.create_service()

    def test_create_service_with_openai_validates_api_key(self):
        """Test that OpenAI API key validation works."""
        with patch('app.services.ai_service_factory.settings') as mock_settings:
            mock_settings.ai_provider = "openai"
            mock_settings.openai_api_key = None  # No API key
            mock_settings.gemini_api_key = None  # No fallback either

            factory = AIServiceFactory()

            with pytest.raises(AIServiceError, match="Failed to create any AI service"):
                factory.create_service()

    def test_get_available_providers_returns_correct_list(self):
        """Test that available providers are correctly identified."""
        with patch('app.services.ai_service_factory.settings') as mock_settings:
            mock_settings.gemini_api_key = "test_gemini_key"
            mock_settings.openai_api_key = "test_openai_key"

            factory = AIServiceFactory()
            providers = factory.get_available_providers()

            assert "gemini" in providers
            assert "openai" in providers
            assert len(providers) == 2

    def test_get_available_providers_with_missing_keys(self):
        """Test available providers when some API keys are missing."""
        with patch('app.services.ai_service_factory.settings') as mock_settings:
            mock_settings.gemini_api_key = "test_gemini_key"
            mock_settings.openai_api_key = None

            factory = AIServiceFactory()
            providers = factory.get_available_providers()

            assert "gemini" in providers
            assert "openai" not in providers
            assert len(providers) == 1

    def test_get_provider_capabilities(self):
        """Test getting capabilities for each provider."""
        factory = AIServiceFactory()

        # Test Gemini capabilities
        gemini_caps = factory.get_provider_capabilities("gemini")
        assert gemini_caps["supports_vision"] is True
        assert gemini_caps["name"] == "gemini"

        # Test OpenAI capabilities with vision model
        with patch('app.services.ai_service_factory.settings') as mock_settings:
            mock_settings.openai_model = "gpt-4-vision-preview"
            openai_caps = factory.get_provider_capabilities("openai")
            assert openai_caps["supports_vision"] is True
            assert openai_caps["name"] == "openai"

        # Test OpenAI capabilities with text model
        with patch('app.services.ai_service_factory.settings') as mock_settings:
            mock_settings.openai_model = "gpt-4"
            openai_caps = factory.get_provider_capabilities("openai")
            assert openai_caps["supports_vision"] is False

    def test_get_provider_capabilities_invalid_provider(self):
        """Test getting capabilities for invalid provider."""
        factory = AIServiceFactory()

        with pytest.raises(AIServiceError, match="Unknown provider"):
            factory.get_provider_capabilities("invalid_provider")

    def test_factory_caches_service_instance(self):
        """Test that factory caches created service instances."""
        with patch('app.services.ai_service_factory.settings') as mock_settings, \
             patch('app.services.ai_service_factory.GeminiService') as mock_gemini:

            mock_settings.ai_provider = "gemini"
            mock_settings.gemini_api_key = "test_gemini_key"

            mock_service = Mock(spec=AIStoryEnhancementService)
            mock_gemini.return_value = mock_service

            factory = AIServiceFactory()

            # First call should create service
            service1 = factory.create_service()
            assert service1 == mock_service
            mock_gemini.assert_called_once()

            # Second call should return cached instance
            service2 = factory.create_service()
            assert service2 == mock_service
            assert service1 is service2
            # Should not call GeminiService constructor again
            mock_gemini.assert_called_once()

    def test_factory_clears_cache_when_requested(self):
        """Test that factory can clear cache and recreate service."""
        with patch('app.services.ai_service_factory.settings') as mock_settings, \
             patch('app.services.ai_service_factory.GeminiService') as mock_gemini:

            mock_settings.ai_provider = "gemini"
            mock_settings.gemini_api_key = "test_gemini_key"

            mock_service1 = Mock(spec=AIStoryEnhancementService)
            mock_service2 = Mock(spec=AIStoryEnhancementService)
            mock_gemini.side_effect = [mock_service1, mock_service2]

            factory = AIServiceFactory()

            # First call
            service1 = factory.create_service()
            assert service1 == mock_service1

            # Clear cache and create new service
            factory.clear_cache()
            service2 = factory.create_service()
            assert service2 == mock_service2
            assert service1 is not service2

            # Should have called constructor twice
            assert mock_gemini.call_count == 2


@pytest.mark.unit
class TestAIServiceError:
    """Test AIServiceError exception class."""

    def test_ai_service_error_creation(self):
        """Test creating AIServiceError with message."""
        error = AIServiceError("Test error message")
        assert str(error) == "Test error message"

    def test_ai_service_error_inheritance(self):
        """Test that AIServiceError inherits from Exception."""
        error = AIServiceError("Test")
        assert isinstance(error, Exception)
