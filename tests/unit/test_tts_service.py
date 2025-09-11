"""Unit tests for Text-to-Speech service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import base64
import os
from app.services.tts_service import TTSService, TTSError


class TestTTSService:
    """Test suite for TTSService."""

    def test_init_with_openai_client(self):
        """Test initialization with OpenAI client."""
        mock_openai = Mock()

        with patch('app.services.tts_service.OPENAI_AVAILABLE', True):
            with patch('app.services.tts_service.settings.openai_api_key', 'test-key'):
                with patch('app.services.tts_service.openai.OpenAI', return_value=mock_openai):
                    service = TTSService()
                    assert service.openai_client == mock_openai

    def test_init_with_elevenlabs_client(self):
        """Test initialization with ElevenLabs client."""
        mock_elevenlabs = Mock()

        with patch('app.services.tts_service.ELEVENLABS_AVAILABLE', True):
            with patch('app.services.tts_service.settings.elevenlabs_api_key', 'test-key'):
                with patch('app.services.tts_service.ElevenLabs', return_value=mock_elevenlabs):
                    service = TTSService()
                    assert service.elevenlabs_client == mock_elevenlabs

    def test_init_without_api_keys(self):
        """Test initialization without API keys."""
        with patch('app.services.tts_service.OPENAI_AVAILABLE', True):
            with patch('app.services.tts_service.ELEVENLABS_AVAILABLE', True):
                with patch('app.services.tts_service.settings.openai_api_key', None):
                    with patch('app.services.tts_service.settings.elevenlabs_api_key', None):
                        service = TTSService()
                        assert service.openai_client is None
                        assert service.elevenlabs_client is None

    def test_init_libraries_not_available(self):
        """Test initialization when libraries are not available."""
        with patch('app.services.tts_service.OPENAI_AVAILABLE', False):
            with patch('app.services.tts_service.ELEVENLABS_AVAILABLE', False):
                service = TTSService()
                assert service.openai_client is None
                assert service.elevenlabs_client is None

    @pytest.mark.asyncio
    async def test_generate_audio_empty_text(self):
        """Test generate_audio with empty text."""
        service = TTSService()

        with pytest.raises(TTSError, match="Text content is required"):
            await service.generate_audio("")

        with pytest.raises(TTSError, match="Text content is required"):
            await service.generate_audio("   ")

    @pytest.mark.asyncio
    async def test_generate_audio_text_truncation(self):
        """Test that long text is truncated."""
        service = TTSService()
        long_text = "a" * 5000  # Over 4096 character limit

        # Mock the provider to capture the truncated text
        service.openai_client = Mock()
        mock_response = Mock()
        mock_response.content = b"audio_data"
        service.openai_client.audio.speech.create.return_value = mock_response

        with patch('app.services.tts_service.settings.tts_provider', 'openai'):
            result, format = await service.generate_audio(long_text)

            # Check that text was truncated
            call_args = service.openai_client.audio.speech.create.call_args
            actual_text = call_args[1]['input']
            assert len(actual_text) <= 4099  # 4096 + "..."
            assert actual_text.endswith("...")

    @pytest.mark.asyncio
    async def test_generate_audio_with_openai_success(self):
        """Test successful audio generation with OpenAI."""
        service = TTSService()

        # Mock OpenAI client
        service.openai_client = Mock()
        mock_response = Mock()
        mock_response.content = b"test_audio_data"
        service.openai_client.audio.speech.create.return_value = mock_response

        with patch('app.services.tts_service.settings.tts_provider', 'openai'):
            with patch('app.services.tts_service.settings.tts_voice', 'alloy'):
                result, format = await service.generate_audio("Test text")

                expected_base64 = base64.b64encode(b"test_audio_data").decode('utf-8')
                assert result == expected_base64
                assert format == "mp3"

                # Verify OpenAI was called correctly
                service.openai_client.audio.speech.create.assert_called_once_with(
                    model="tts-1",
                    voice="alloy",
                    input="Test text",
                    response_format="mp3"
                )

    @pytest.mark.asyncio
    async def test_generate_audio_with_openai_rate_limit(self):
        """Test OpenAI rate limit error handling."""
        service = TTSService()

        # Mock OpenAI client to raise rate limit error
        service.openai_client = Mock()
        service.openai_client.audio.speech.create.side_effect = Exception("Rate limit exceeded")

        with patch('app.services.tts_service.settings.tts_provider', 'openai'):
            with pytest.raises(TTSError, match="rate limit exceeded"):
                await service.generate_audio("Test text")

    @pytest.mark.asyncio
    async def test_generate_audio_with_openai_quota_exceeded(self):
        """Test OpenAI quota exceeded error handling."""
        service = TTSService()

        # Mock OpenAI client to raise quota error
        service.openai_client = Mock()
        service.openai_client.audio.speech.create.side_effect = Exception("Quota exceeded")

        with patch('app.services.tts_service.settings.tts_provider', 'openai'):
            with pytest.raises(TTSError, match="quota exceeded"):
                await service.generate_audio("Test text")

    @pytest.mark.asyncio
    async def test_generate_audio_with_openai_auth_error(self):
        """Test OpenAI authentication error handling."""
        service = TTSService()

        # Mock OpenAI client to raise auth error
        service.openai_client = Mock()
        service.openai_client.audio.speech.create.side_effect = Exception("Invalid API key")

        with patch('app.services.tts_service.settings.tts_provider', 'openai'):
            with pytest.raises(TTSError, match="authentication failed"):
                await service.generate_audio("Test text")

    @pytest.mark.asyncio
    async def test_generate_audio_with_openai_generic_error(self):
        """Test OpenAI generic error handling."""
        service = TTSService()

        # Mock OpenAI client to raise generic error
        service.openai_client = Mock()
        service.openai_client.audio.speech.create.side_effect = Exception("Unknown error")

        with patch('app.services.tts_service.settings.tts_provider', 'openai'):
            with pytest.raises(TTSError, match="OpenAI TTS generation failed: Unknown error"):
                await service.generate_audio("Test text")

    @pytest.mark.asyncio
    async def test_generate_audio_with_invalid_voice(self):
        """Test audio generation with invalid voice name."""
        service = TTSService()

        # Mock OpenAI client
        service.openai_client = Mock()
        mock_response = Mock()
        mock_response.content = b"test_audio_data"
        service.openai_client.audio.speech.create.return_value = mock_response

        with patch('app.services.tts_service.settings.tts_provider', 'openai'):
            result, format = await service.generate_audio("Test text", voice="invalid_voice")

            # Should fall back to "alloy"
            service.openai_client.audio.speech.create.assert_called_once()
            call_args = service.openai_client.audio.speech.create.call_args
            assert call_args[1]['voice'] == 'alloy'

    @pytest.mark.asyncio
    async def test_generate_audio_fallback_to_mock(self):
        """Test fallback to mock audio when no provider is available."""
        service = TTSService()
        service.openai_client = None
        service.elevenlabs_client = None

        with patch('app.services.tts_service.settings.tts_provider', 'openai'):
            result, format = await service.generate_audio("Test text")

            # Mock should return base64 encoded data
            assert isinstance(result, str)
            assert format == "mp3"

            # Verify it's valid base64
            try:
                base64.b64decode(result)
            except Exception:
                pytest.fail("Result is not valid base64")

    @pytest.mark.asyncio
    async def test_generate_audio_with_elevenlabs(self):
        """Test ElevenLabs audio generation with mock client."""
        service = TTSService()

        # Mock ElevenLabs client properly
        mock_elevenlabs_client = Mock()
        mock_response = Mock()
        mock_response.__iter__ = Mock(return_value=iter([b"test", b"audio", b"data"]))
        mock_elevenlabs_client.text_to_speech.convert.return_value = mock_response
        service.elevenlabs_client = mock_elevenlabs_client

        with patch('app.services.tts_service.settings.tts_provider', 'elevenlabs'):
            result, format = await service.generate_audio("Test text")

            # Should return base64 encoded audio
            expected_base64 = base64.b64encode(b"testaudiodata").decode('utf-8')
            assert result == expected_base64
            assert format == "mp3"

    def test_get_supported_languages(self):
        """Test getting supported languages."""
        service = TTSService()

        # Check that common languages are supported
        languages = service.get_supported_languages()
        assert isinstance(languages, list)
        assert 'en' in languages
        assert 'es' in languages
        assert 'fr' in languages

    def test_get_available_voices(self):
        """Test getting available voices."""
        service = TTSService()

        # Test with no provider specified
        voices = service.get_available_voices()
        assert isinstance(voices, dict)

        # Test with OpenAI provider
        voices_openai = service.get_available_voices(provider="openai")
        assert "openai" in voices_openai
        voice_names = [v["name"] for v in voices_openai["openai"]]
        assert 'alloy' in voice_names
        assert 'echo' in voice_names
        assert 'nova' in voice_names

    @pytest.mark.asyncio
    async def test_test_service_with_openai(self):
        """Test the test_service method with OpenAI available."""
        service = TTSService()
        service.openai_client = Mock()

        # Mock the audio generation
        with patch.object(service, '_generate_openai_audio', return_value=("base64_data", "mp3")):
            result = await service.test_service()
            assert isinstance(result, dict)
            assert result["openai"]["available"] is True
            assert result["openai"]["working"] is True

    @pytest.mark.asyncio
    async def test_test_service_with_elevenlabs(self):
        """Test the test_service method with ElevenLabs available."""
        service = TTSService()
        service.elevenlabs_client = Mock()

        # Mock the audio generation
        with patch.object(service, '_generate_elevenlabs_audio', return_value=("base64_data", "mp3")):
            result = await service.test_service()
            assert isinstance(result, dict)
            assert result["elevenlabs"]["available"] is True
            assert result["elevenlabs"]["working"] is True

    @pytest.mark.asyncio
    async def test_test_service_no_clients(self):
        """Test the test_service method with no clients available."""
        service = TTSService()
        service.openai_client = None
        service.elevenlabs_client = None

        result = await service.test_service()
        assert isinstance(result, dict)
        assert result["openai"]["available"] is False
        assert result["elevenlabs"]["available"] is False
