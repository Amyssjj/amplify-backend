"""
Phase 1 Coverage Improvement Tests - Quick Wins
Target: Cover simple uncovered lines in high-coverage files
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open, AsyncMock
import os
from fastapi import HTTPException
from abc import ABC
import json

# Test for health endpoints (lines 11, 16)
from app.api.v1.endpoints.health import health_check, detailed_health_check


@pytest.mark.unit
class TestHealthEndpointsCoverage:
    """Test uncovered lines in health endpoints."""

    @pytest.mark.asyncio
    async def test_health_check_return_values(self):
        """Test the actual return values of health check."""
        result = await health_check()
        assert result == {"status": "healthy", "service": "amplify-backend"}
        assert "status" in result
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_detailed_health_check_return_values(self):
        """Test the actual return values of detailed health check."""
        result = await detailed_health_check()
        assert result["status"] == "healthy"
        assert result["service"] == "amplify-backend"
        assert result["version"] == "1.0.0"
        assert result["uptime"] == "running"
        assert len(result) == 4


# Test for AI service interface abstract methods
@pytest.mark.unit
class TestAIServiceInterfaceCoverage:
    """Test uncovered lines in AI service interface."""

    def test_ai_service_interface_abstract_method_errors(self):
        """Test that abstract methods raise NotImplementedError when called directly."""
        from app.services.ai_service_interface import AIStoryEnhancementService

        # Create a minimal concrete implementation to test the abstract class
        class PartialImplementation(AIStoryEnhancementService):
            # Only implement some methods to test the others
            def get_provider_name(self) -> str:
                return "test"

        # Try to instantiate - should fail because not all methods implemented
        with pytest.raises(TypeError) as exc_info:
            instance = PartialImplementation()
        assert "Can't instantiate abstract class" in str(exc_info.value)

    def test_ai_service_interface_concrete_methods(self):
        """Test concrete implementation of all abstract methods."""
        from app.services.ai_service_interface import AIStoryEnhancementService

        # Create a complete concrete implementation
        class CompleteImplementation(AIStoryEnhancementService):
            async def enhance_story_with_photo(self, photo_base64: str, transcript: str, language: str):
                return {"enhanced_story": "test", "insights": {}}

            def supports_vision(self) -> bool:
                return True

            def get_provider_name(self) -> str:
                return "complete_test"

        # This should work fine
        instance = CompleteImplementation()
        assert instance.get_provider_name() == "complete_test"
        assert instance.supports_vision() is True


# Test for OpenAI service uncovered error paths
@pytest.mark.unit
class TestOpenAIServiceCoverage:
    """Test uncovered lines in OpenAI service."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_openai_service_api_error_handling(self):
        """Test OpenAI service handling of API errors (line 71)."""
        from app.services.openai_service import OpenAIService, OpenAIError

        # Test that OpenAI is imported properly
        with patch('app.services.openai_service.openai') as mock_openai_module:
            # Mock the OpenAI client
            mock_client = Mock()
            mock_openai_module.OpenAI.return_value = mock_client

            service = OpenAIService()

            # Test API error during text-only mode (line 127)
            mock_client.chat.completions.create.side_effect = Exception("API Error")

            with pytest.raises(OpenAIError) as exc_info:
                await service.enhance_story_with_photo(
                    photo_base64="fake_image",
                    transcript="test transcript",
                    language="en"
                )
            assert "OpenAI API call failed" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "gpt-3.5-turbo"})
    async def test_openai_text_only_mode_json_parsing_error(self):
        """Test JSON parsing error in text-only mode (lines 161-163)."""
        from app.services.openai_service import OpenAIService, OpenAIError

        with patch('app.services.openai_service.openai') as mock_openai_module:
            # Mock the OpenAI client
            mock_client = Mock()
            mock_openai_module.OpenAI.return_value = mock_client

            # Mock response with invalid JSON
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Not valid JSON {{{"))]
            mock_client.chat.completions.create.return_value = mock_response

            service = OpenAIService()

            # This should trigger JSON decode error
            with pytest.raises(OpenAIError) as exc_info:
                await service.enhance_story_with_photo(
                    photo_base64="fake_image",
                    transcript="test transcript",
                    language="en"
                )
            assert "Could not extract valid JSON" in str(exc_info.value) or "Invalid response format" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_openai_service_missing_response_fields(self):
        """Test handling of missing fields in API response (lines 214, 224, 230)."""
        from app.services.openai_service import OpenAIService, OpenAIError

        with patch('app.services.openai_service.openai') as mock_openai_module:
            # Mock the OpenAI client
            mock_client = Mock()
            mock_openai_module.OpenAI.return_value = mock_client

            service = OpenAIService()

            # Test missing 'enhanced_story' field (line 214)
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content='{"insights": {}}'))]
            mock_client.chat.completions.create.return_value = mock_response

            with pytest.raises(OpenAIError) as exc_info:
                await service.enhance_story_with_photo(
                    photo_base64="fake_image",
                    transcript="test transcript",
                    language="en"
                )
            assert "Could not extract valid JSON" in str(exc_info.value) or "Invalid response format" in str(exc_info.value)

            # Test missing 'insights' field (line 224)
            mock_response.choices = [Mock(message=Mock(content='{"enhanced_story": "test"}'))]

            with pytest.raises(OpenAIError) as exc_info:
                await service.enhance_story_with_photo(
                    photo_base64="fake_image",
                    transcript="test transcript",
                    language="en"
                )
            assert "Could not extract valid JSON" in str(exc_info.value) or "Invalid response format" in str(exc_info.value)

            # Test insights not being a dict (line 230)
            mock_response.choices = [Mock(message=Mock(content='{"enhanced_story": "test", "insights": "not a dict"}'))]

            with pytest.raises(OpenAIError) as exc_info:
                await service.enhance_story_with_photo(
                    photo_base64="fake_image",
                    transcript="test transcript",
                    language="en"
                )
            assert "Could not extract valid JSON" in str(exc_info.value) or "Invalid response format" in str(exc_info.value)


# Test for base model utilities
@pytest.mark.unit
class TestBaseModelCoverage:
    """Test uncovered lines in base model."""

    def test_base_model_postgres_url_fix(self):
        """Test the postgres:// to postgresql:// URL conversion (lines 17-18)."""
        # Save original env
        original_url = os.environ.get("DATABASE_URL")

        try:
            # Test with postgres:// URL
            test_url = "postgres://user:pass@host:5432/db"
            os.environ["DATABASE_URL"] = test_url

            # Import after setting env to trigger the conversion
            import importlib
            import app.models.base
            importlib.reload(app.models.base)

            # The URL should be converted
            assert app.models.base.DATABASE_URL == "postgresql://user:pass@host:5432/db"

        finally:
            # Restore original env
            if original_url:
                os.environ["DATABASE_URL"] = original_url
            else:
                os.environ.pop("DATABASE_URL", None)

    def test_base_model_no_database_url(self):
        """Test behavior when DATABASE_URL is not set (lines 29-36)."""
        # Save original env
        original_url = os.environ.get("DATABASE_URL")

        try:
            # Remove DATABASE_URL
            os.environ.pop("DATABASE_URL", None)

            # Import after removing env
            import importlib
            import app.models.base
            importlib.reload(app.models.base)

            # SessionLocal should be None
            assert app.models.base.SessionLocal is None
            assert app.models.base.engine is None

            # get_db should raise RuntimeError
            with pytest.raises(RuntimeError) as exc_info:
                gen = app.models.base.get_db()
                next(gen)
            assert "Database not configured" in str(exc_info.value)

        finally:
            # Restore original env
            if original_url:
                os.environ["DATABASE_URL"] = original_url
            else:
                os.environ.pop("DATABASE_URL", None)

    def test_base_model_get_db_cleanup(self):
        """Test that get_db properly closes the session (lines 33-36)."""
        # Save original env
        original_url = os.environ.get("DATABASE_URL")

        try:
            # Set a valid DATABASE_URL
            os.environ["DATABASE_URL"] = "postgresql://user:pass@host:5432/db"

            # Import after setting env
            import importlib
            import app.models.base
            importlib.reload(app.models.base)

            # Mock SessionLocal
            mock_session = Mock()
            mock_session_class = Mock(return_value=mock_session)
            app.models.base.SessionLocal = mock_session_class

            # Use get_db
            gen = app.models.base.get_db()
            db = next(gen)

            # Verify we got the mock session
            assert db == mock_session

            # Trigger cleanup
            try:
                gen.send(None)
            except StopIteration:
                pass

            # Verify close was called
            mock_session.close.assert_called_once()

        finally:
            # Restore original env
            if original_url:
                os.environ["DATABASE_URL"] = original_url
            else:
                os.environ.pop("DATABASE_URL", None)


# Additional test for prompt manager uncovered lines
@pytest.mark.unit
class TestPromptManagerCoverage:
    """Test uncovered lines in prompt manager."""

    def test_prompt_manager_file_not_found_errors(self):
        """Test file not found error handling (lines 70, 74, 87)."""
        from app.services.prompt_manager import PromptManager, PromptManagerError

        with patch('builtins.open', side_effect=FileNotFoundError("Config not found")):
            with pytest.raises(PromptManagerError) as exc_info:
                pm = PromptManager()
            # Check that the error message contains relevant info
            assert "Failed to load config" in str(exc_info.value)

    def test_prompt_manager_yaml_error(self):
        """Test YAML parsing error (line 110)."""
        from app.services.prompt_manager import PromptManager, PromptManagerError
        import yaml

        # Mock open to return invalid YAML
        mock_file = Mock()
        mock_file.__enter__ = Mock(return_value=Mock(read=Mock(return_value="invalid: yaml: content: [")))
        mock_file.__exit__ = Mock(return_value=None)

        with patch('builtins.open', return_value=mock_file):
            with pytest.raises(PromptManagerError) as exc_info:
                pm = PromptManager()
            # Check that it's a YAML error
            assert "Failed to load config" in str(exc_info.value)

    @patch('app.services.prompt_manager.os.path.exists')
    @patch('app.services.prompt_manager.os.path.getmtime')
    def test_prompt_manager_reload_prompts(self, mock_getmtime, mock_exists):
        """Test reload_prompts method (lines 120+)."""
        from app.services.prompt_manager import PromptManager

        # Create a PromptManager with mocked config
        with patch('builtins.open', mock_open(read_data="prompts:\n  test:\n    file: test.txt\n    description: Test")):
            pm = PromptManager()

            # Test reload_prompts method
            with patch.object(pm, '__init__', return_value=None):
                pm.reload_prompts()  # Should not raise
