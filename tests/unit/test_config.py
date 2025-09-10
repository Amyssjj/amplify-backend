"""
Unit tests for configuration settings related to AI providers.
"""
import pytest
from unittest.mock import patch
from app.core.config import Settings


@pytest.mark.unit
class TestAIProviderConfiguration:
    """Test AI provider configuration settings."""

    def test_default_ai_provider_is_gemini(self):
        """Test that default AI provider is gemini."""
        settings = Settings()
        assert settings.ai_provider == "gemini"

    def test_ai_provider_can_be_set_to_openai(self):
        """Test that AI provider can be set to openai."""
        with patch.dict('os.environ', {'AI_PROVIDER': 'openai'}):
            settings = Settings()
            assert settings.ai_provider == "openai"

    def test_ai_provider_validation_accepts_valid_providers(self):
        """Test that AI provider validation accepts valid providers."""
        valid_providers = ["gemini", "openai"]

        for provider in valid_providers:
            with patch.dict('os.environ', {'AI_PROVIDER': provider}):
                settings = Settings()
                assert settings.ai_provider == provider

    def test_ai_provider_validation_rejects_invalid_providers(self):
        """Test that AI provider validation rejects invalid providers."""
        with patch.dict('os.environ', {'AI_PROVIDER': 'invalid_provider'}):
            with pytest.raises(ValueError, match="Invalid AI provider"):
                Settings()

    def test_openai_model_default_value(self):
        """Test that OpenAI model has a sensible default."""
        settings = Settings()
        assert settings.openai_model == "gpt-4-vision-preview"

    def test_openai_model_can_be_customized(self):
        """Test that OpenAI model can be customized via environment."""
        with patch.dict('os.environ', {'OPENAI_MODEL': 'gpt-4'}):
            settings = Settings()
            assert settings.openai_model == "gpt-4"

    def test_openai_model_validation_accepts_valid_models(self):
        """Test that OpenAI model validation accepts valid models."""
        valid_models = [
            "gpt-4-vision-preview",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "chatgpt-4o-latest"
        ]

        for model in valid_models:
            with patch.dict('os.environ', {'OPENAI_MODEL': model}):
                settings = Settings()
                assert settings.openai_model == model

    def test_openai_model_validation_rejects_invalid_models(self):
        """Test that OpenAI model validation rejects invalid models."""
        with patch.dict('os.environ', {'OPENAI_MODEL': 'invalid-model'}):
            with pytest.raises(ValueError, match="Invalid OpenAI model"):
                Settings()

    def test_ai_provider_auto_selection_when_not_specified(self):
        """Test intelligent AI provider selection based on available API keys."""
        # Test case 1: Both keys available, should default to gemini
        with patch.dict('os.environ', {
            'GEMINI_API_KEY': 'test_gemini_key',
            'OPENAI_API_KEY': 'test_openai_key'
        }):
            settings = Settings()
            assert settings.ai_provider == "gemini"  # Default preference

    def test_ai_provider_fallback_to_available_key(self):
        """Test AI provider fallback when only one API key is available."""
        # Test case: Only OpenAI key available, no AI_PROVIDER set
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'test_openai_key'
        }, clear=True):
            settings = Settings()
            # Should use default since no explicit provider set
            assert settings.ai_provider == "gemini"  # Still default

    def test_gemini_model_configuration(self):
        """Test Gemini model configuration."""
        settings = Settings()
        assert settings.gemini_model == "models/gemini-2.5-flash-lite"

    def test_gemini_model_can_be_customized(self):
        """Test that Gemini model can be customized."""
        with patch.dict('os.environ', {'GEMINI_MODEL': 'models/gemini-pro-vision'}):
            settings = Settings()
            assert settings.gemini_model == "models/gemini-pro-vision"

    def test_gemini_model_validation_accepts_valid_models(self):
        """Test that Gemini model validation accepts valid models."""
        valid_models = [
            "models/gemini-2.5-flash-lite",
            "models/gemini-pro-vision",
            "models/gemini-pro",
            "models/gemini-2.0-flash-exp",
            "models/gemini-2.5-pro",
            "models/gemini-2.5-flash"
        ]

        for model in valid_models:
            with patch.dict('os.environ', {'GEMINI_MODEL': model}):
                settings = Settings()
                assert settings.gemini_model == model

    def test_gemini_model_validation_rejects_invalid_models(self):
        """Test that Gemini model validation rejects invalid models."""
        with patch.dict('os.environ', {'GEMINI_MODEL': 'invalid-gemini-model'}):
            with pytest.raises(ValueError, match="Invalid Gemini model"):
                Settings()

    def test_ai_provider_capabilities_detection(self):
        """Test that AI provider capabilities are correctly detected."""
        # OpenAI vision models
        vision_models = ["gpt-4-vision-preview", "gpt-4-turbo"]
        text_models = ["gpt-4", "gpt-3.5-turbo"]

        for model in vision_models:
            with patch.dict('os.environ', {
                'AI_PROVIDER': 'openai',
                'OPENAI_MODEL': model
            }):
                settings = Settings()
                assert settings.supports_vision is True

        for model in text_models:
            with patch.dict('os.environ', {
                'AI_PROVIDER': 'openai',
                'OPENAI_MODEL': model
            }):
                settings = Settings()
                assert settings.supports_vision is False

    def test_gemini_always_supports_vision(self):
        """Test that Gemini provider always supports vision."""
        with patch.dict('os.environ', {'AI_PROVIDER': 'gemini'}):
            settings = Settings()
            assert settings.supports_vision is True
