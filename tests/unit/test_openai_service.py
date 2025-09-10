"""
Unit tests for OpenAI story enhancement service.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import base64
from app.services.openai_service import OpenAIService, OpenAIError
from app.schemas.ai_response import AIResponse
from app.services.ai_service_interface import AIStoryEnhancementService


@pytest.mark.unit
class TestOpenAIService:
    """Test OpenAI service functionality."""

    @pytest.fixture
    def openai_service(self):
        """Create OpenAIService instance for testing."""
        with patch('app.services.openai_service.openai') as mock_openai:
            mock_client = Mock()
            mock_openai.OpenAI.return_value = mock_client
            return OpenAIService(api_key="test_api_key", model="gpt-4-vision-preview")

    @pytest.fixture
    def sample_photo_base64(self):
        """Sample base64 encoded image for testing."""
        # Create a simple 1x1 pixel PNG in base64
        return base64.b64encode(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x01\x00\x00\x00\x007n\xf9$\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\r\n\x1d\xb3\x00\x00\x00\x00IEND\xaeB`\x82'
        ).decode('utf-8')

    @pytest.fixture
    def sample_transcript(self):
        """Sample story transcript for testing."""
        return "Once upon a time, there was a brave knight who embarked on a quest to save the kingdom."

    @pytest.fixture
    def expected_openai_response(self):
        """Expected response structure from OpenAI API."""
        return {
            "enhanced_transcript": "Once upon a time, in a realm shrouded by morning mist, there lived Sir Gareth, a brave knight whose armor gleamed like silver moonlight. With unwavering determination burning in his emerald eyes, he embarked upon a perilous quest to save the kingdom from an ancient curse that had befallen the land.",
            "insights": {
                "plot": "Enhanced the basic quest structure with specific conflict (ancient curse) and clearer stakes",
                "character": "Added character name (Sir Gareth) and physical descriptions to create more vivid protagonist",
                "setting": "Incorporated atmospheric details like morning mist and specific time period to establish mood",
                "mood": "Elevated the tone from simple narrative to more dramatic and immersive fantasy style"
            }
        }

    def test_openai_service_implements_interface(self, openai_service):
        """Test that OpenAIService implements AIStoryEnhancementService interface."""
        assert isinstance(openai_service, AIStoryEnhancementService)

    def test_openai_service_initialization_with_api_key(self):
        """Test OpenAI service initialization with API key."""
        with patch('app.services.openai_service.openai') as mock_openai:
            mock_client = Mock()
            mock_openai.OpenAI.return_value = mock_client

            service = OpenAIService(api_key="test_key", model="gpt-4")

            mock_openai.OpenAI.assert_called_once_with(api_key="test_key")
            assert service.model == "gpt-4"

    def test_openai_service_initialization_without_api_key_raises_error(self):
        """Test that OpenAI service raises error when no API key provided."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(OpenAIError, match="OPENAI_API_KEY environment variable is required"):
                OpenAIService()

    def test_openai_service_supports_vision_with_vision_model(self):
        """Test that OpenAI service supports vision with vision-capable models."""
        with patch('app.services.openai_service.openai'):
            vision_models = ["gpt-4-vision-preview", "gpt-4-turbo"]

            for model in vision_models:
                service = OpenAIService(api_key="test_key", model=model)
                assert service.supports_vision() is True

    def test_openai_service_supports_vision_with_text_model(self):
        """Test that OpenAI service doesn't support vision with text-only models."""
        with patch('app.services.openai_service.openai'):
            text_models = ["gpt-4", "gpt-3.5-turbo"]

            for model in text_models:
                service = OpenAIService(api_key="test_key", model=model)
                assert service.supports_vision() is False

    def test_openai_service_provider_name(self, openai_service):
        """Test that OpenAI service returns correct provider name."""
        assert openai_service.get_provider_name() == "openai"

    async def test_enhance_story_with_photo_success_vision_model(self, openai_service, sample_photo_base64, sample_transcript, expected_openai_response):
        """Test successful story enhancement with photo analysis using vision model."""
        # Mock OpenAI API response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = '```json\n' + str(expected_openai_response).replace("'", '"') + '\n```'

        openai_service.client.chat.completions.create = Mock(return_value=mock_response)

        result = await openai_service.enhance_story_with_photo(
            photo_base64=sample_photo_base64,
            transcript=sample_transcript,
            language="en"
        )

        # Verify result structure
        assert isinstance(result, AIResponse)
        assert result.enhanced_transcript == expected_openai_response["enhanced_transcript"]
        assert result.insights == expected_openai_response["insights"]

        # Verify API was called with vision
        openai_service.client.chat.completions.create.assert_called_once()
        call_args = openai_service.client.chat.completions.create.call_args[1]
        assert "vision" in str(call_args).lower() or len(call_args["messages"][0]["content"]) > 1

    async def test_enhance_story_with_photo_text_only_fallback(self, sample_photo_base64, sample_transcript):
        """Test fallback to text-only processing when vision is not available."""
        with patch('app.services.openai_service.openai') as mock_openai:
            mock_client = Mock()
            mock_openai.OpenAI.return_value = mock_client

            service = OpenAIService(api_key="test_key", model="gpt-4")  # Text-only model

            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = '{"enhanced_transcript": "Enhanced story", "insights": {"test": "insight"}}'

            service.client.chat.completions.create = Mock(return_value=mock_response)

            result = await service.enhance_story_with_photo(
                photo_base64=sample_photo_base64,
                transcript=sample_transcript,
                language="en"
            )

            assert isinstance(result, AIResponse)
            # Should still work but without image analysis
            service.client.chat.completions.create.assert_called_once()

    async def test_enhance_story_with_photo_api_error(self, openai_service, sample_photo_base64, sample_transcript):
        """Test handling of OpenAI API errors."""
        openai_service.client.chat.completions.create = Mock(side_effect=Exception("API rate limit exceeded"))

        with pytest.raises(OpenAIError, match="OpenAI API call failed"):
            await openai_service.enhance_story_with_photo(
                photo_base64=sample_photo_base64,
                transcript=sample_transcript,
                language="en"
            )

    async def test_enhance_story_with_photo_invalid_json_response(self, openai_service, sample_photo_base64, sample_transcript):
        """Test handling of invalid JSON response from OpenAI."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "This is not valid JSON"

        openai_service.client.chat.completions.create = Mock(return_value=mock_response)

        with pytest.raises(OpenAIError, match="Could not extract valid JSON"):
            await openai_service.enhance_story_with_photo(
                photo_base64=sample_photo_base64,
                transcript=sample_transcript,
                language="en"
            )

    def test_validate_inputs_success(self, openai_service, sample_photo_base64, sample_transcript):
        """Test input validation with valid inputs."""
        # Should not raise any exceptions
        openai_service._validate_inputs(
            photo_base64=sample_photo_base64,
            transcript=sample_transcript,
            language="en"
        )

    def test_validate_inputs_empty_photo(self, openai_service, sample_transcript):
        """Test input validation with empty photo."""
        with pytest.raises(OpenAIError, match="Photo data is required"):
            openai_service._validate_inputs(
                photo_base64="",
                transcript=sample_transcript,
                language="en"
            )

    def test_validate_inputs_empty_transcript(self, openai_service, sample_photo_base64):
        """Test input validation with empty transcript."""
        with pytest.raises(OpenAIError, match="Transcript is required"):
            openai_service._validate_inputs(
                photo_base64=sample_photo_base64,
                transcript="",
                language="en"
            )

    def test_validate_inputs_invalid_language(self, openai_service, sample_photo_base64, sample_transcript):
        """Test input validation with invalid language code."""
        with pytest.raises(OpenAIError, match="Invalid language code"):
            openai_service._validate_inputs(
                photo_base64=sample_photo_base64,
                transcript=sample_transcript,
                language="invalid"
            )

    def test_validate_inputs_transcript_too_long(self, openai_service, sample_photo_base64):
        """Test input validation with transcript that's too long."""
        long_transcript = "x" * 5001  # Exceeds 5000 char limit

        with pytest.raises(OpenAIError, match="Transcript too long"):
            openai_service._validate_inputs(
                photo_base64=sample_photo_base64,
                transcript=long_transcript,
                language="en"
            )

    def test_build_prompt_with_transcript_and_language(self, openai_service, sample_transcript):
        """Test that prompt is built with transcript and language."""
        with patch('app.services.openai_service.prompt_manager') as mock_pm:
            mock_template = Mock()
            mock_template.format.return_value = "Formatted prompt with transcript"
            mock_pm.get_prompt.return_value = mock_template

            prompt = openai_service._build_prompt(
                transcript=sample_transcript,
                language="en"
            )

            # Verify PromptManager was called correctly
            mock_pm.get_prompt.assert_called_once_with("social")
            mock_template.format.assert_called_once_with(
                transcript=sample_transcript,
                language_name="English"
            )
            assert "Formatted prompt with transcript" in prompt
            assert "JSON object containing 'enhanced_transcript' and 'insights'" in prompt

    def test_build_messages_for_vision_model(self, openai_service, sample_photo_base64, sample_transcript):
        """Test building messages for vision-capable model."""
        openai_service.model = "gpt-4-vision-preview"

        messages = openai_service._build_messages(
            prompt="Test prompt",
            photo_base64=sample_photo_base64
        )

        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert isinstance(messages[0]["content"], list)
        assert len(messages[0]["content"]) == 2  # Text + Image

        # Check text content
        text_content = next(item for item in messages[0]["content"] if item["type"] == "text")
        assert text_content["text"] == "Test prompt"

        # Check image content
        image_content = next(item for item in messages[0]["content"] if item["type"] == "image_url")
        assert sample_photo_base64 in image_content["image_url"]["url"]

    def test_build_messages_for_text_model(self, openai_service, sample_photo_base64, sample_transcript):
        """Test building messages for text-only model."""
        openai_service.model = "gpt-4"  # Text-only model

        messages = openai_service._build_messages(
            prompt="Test prompt with image description",
            photo_base64=sample_photo_base64
        )

        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert isinstance(messages[0]["content"], str)
        assert "Test prompt with image description" in messages[0]["content"]
        assert "cannot be analyzed with this model" in messages[0]["content"]


@pytest.mark.unit
class TestOpenAIError:
    """Test OpenAIError exception class."""

    def test_openai_error_creation(self):
        """Test creating OpenAIError with message."""
        error = OpenAIError("Test error message")
        assert str(error) == "Test error message"

    def test_openai_error_inheritance(self):
        """Test that OpenAIError inherits from Exception."""
        error = OpenAIError("Test")
        assert isinstance(error, Exception)
