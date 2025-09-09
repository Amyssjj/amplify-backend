"""
Unit tests for AI service interface and base classes.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from abc import ABC
from app.services.ai_service_interface import AIStoryEnhancementService
from app.schemas.ai_response import AIResponse


@pytest.mark.unit
class TestAIServiceInterface:
    """Test AI service interface and base classes."""

    def test_ai_service_interface_is_abstract(self):
        """Test that AIStoryEnhancementService is an abstract base class."""
        assert issubclass(AIStoryEnhancementService, ABC)

        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            AIStoryEnhancementService()

    def test_ai_service_interface_has_required_methods(self):
        """Test that interface defines required abstract methods."""
        # Get the abstract methods
        abstract_methods = AIStoryEnhancementService.__abstractmethods__

        expected_methods = {
            'enhance_story_with_photo',
            'supports_vision',
            'get_provider_name'
        }

        assert abstract_methods == expected_methods

    def test_concrete_implementation_must_implement_all_methods(self):
        """Test that concrete implementations must implement all abstract methods."""

        class IncompleteService(AIStoryEnhancementService):
            """Incomplete implementation missing required methods."""
            pass

        # Should not be able to instantiate without implementing all methods
        with pytest.raises(TypeError):
            IncompleteService()

    def test_complete_implementation_can_be_instantiated(self):
        """Test that complete implementations can be instantiated."""

        class CompleteService(AIStoryEnhancementService):
            """Complete implementation with all required methods."""

            async def enhance_story_with_photo(self, photo_base64: str, transcript: str, language: str = "en") -> AIResponse:
                return AIResponse(
                    enhanced_transcript="Enhanced story",
                    insights={"test": "insight"}
                )

            def supports_vision(self) -> bool:
                return True

            def get_provider_name(self) -> str:
                return "test_provider"

        # Should be able to instantiate
        service = CompleteService()
        assert service.get_provider_name() == "test_provider"
        assert service.supports_vision() is True

    async def test_enhance_story_with_photo_signature(self):
        """Test enhance_story_with_photo method signature and return type."""

        class TestService(AIStoryEnhancementService):
            async def enhance_story_with_photo(self, photo_base64: str, transcript: str, language: str = "en") -> AIResponse:
                return AIResponse(
                    enhanced_transcript="Test enhanced story",
                    insights={"plot": "Enhanced plot"}
                )

            def supports_vision(self) -> bool:
                return True

            def get_provider_name(self) -> str:
                return "test"

        service = TestService()
        result = await service.enhance_story_with_photo("base64_data", "story", "en")

        assert isinstance(result, AIResponse)
        assert result.enhanced_transcript == "Test enhanced story"
        assert result.insights == {"plot": "Enhanced plot"}

    def test_supports_vision_method(self):
        """Test supports_vision method returns boolean."""

        class VisionService(AIStoryEnhancementService):
            async def enhance_story_with_photo(self, photo_base64: str, transcript: str, language: str = "en") -> AIResponse:
                return AIResponse(enhanced_transcript="", insights={})

            def supports_vision(self) -> bool:
                return True

            def get_provider_name(self) -> str:
                return "vision_provider"

        class TextOnlyService(AIStoryEnhancementService):
            async def enhance_story_with_photo(self, photo_base64: str, transcript: str, language: str = "en") -> AIResponse:
                return AIResponse(enhanced_transcript="", insights={})

            def supports_vision(self) -> bool:
                return False

            def get_provider_name(self) -> str:
                return "text_provider"

        vision_service = VisionService()
        text_service = TextOnlyService()

        assert vision_service.supports_vision() is True
        assert text_service.supports_vision() is False

    def test_get_provider_name_method(self):
        """Test get_provider_name method returns string."""

        class NamedService(AIStoryEnhancementService):
            async def enhance_story_with_photo(self, photo_base64: str, transcript: str, language: str = "en") -> AIResponse:
                return AIResponse(enhanced_transcript="", insights={})

            def supports_vision(self) -> bool:
                return True

            def get_provider_name(self) -> str:
                return "my_ai_provider"

        service = NamedService()
        assert service.get_provider_name() == "my_ai_provider"
        assert isinstance(service.get_provider_name(), str)
