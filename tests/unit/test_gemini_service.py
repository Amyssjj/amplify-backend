"""
Unit tests for Gemini story enhancement service.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import base64
from app.services.gemini_service import GeminiService, GeminiError, GeminiResponse


@pytest.mark.unit
class TestGeminiService:
    """Test Gemini service functionality."""
    
    @pytest.fixture
    def gemini_service(self):
        """Create GeminiService instance for testing."""
        with patch('app.services.gemini_service.genai'):
            return GeminiService(api_key="test_api_key")
    
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
    def expected_gemini_response(self):
        """Expected response structure from Gemini API."""
        return {
            "enhanced_transcript": "Once upon a time, in a realm shrouded by morning mist, there lived Sir Gareth, a brave knight whose armor gleamed like silver moonlight. With unwavering determination burning in his emerald eyes, he embarked upon a perilous quest to save the kingdom from an ancient curse that had befallen the land.",
            "insights": {
                "plot": "Enhanced the basic quest structure with specific conflict (ancient curse) and clearer stakes",
                "character": "Added character name (Sir Gareth) and physical descriptions to create more vivid protagonist", 
                "setting": "Incorporated atmospheric details like morning mist and specific time period to establish mood",
                "mood": "Elevated the tone from simple narrative to more dramatic and immersive fantasy style"
            }
        }
    
    async def test_enhance_story_success(self, gemini_service, sample_photo_base64, sample_transcript, expected_gemini_response):
        """Test successful story enhancement with photo analysis."""
        with patch.object(gemini_service, '_call_gemini_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = expected_gemini_response
            
            result = await gemini_service.enhance_story_with_photo(
                photo_base64=sample_photo_base64,
                transcript=sample_transcript,
                language="en"
            )
            
            # Verify result structure
            assert isinstance(result, GeminiResponse)
            assert result.enhanced_transcript == expected_gemini_response["enhanced_transcript"]
            assert result.insights == expected_gemini_response["insights"]
            
            # Verify API was called with correct parameters
            mock_api.assert_called_once()
            call_args = mock_api.call_args[1]
            assert call_args["photo_base64"] == sample_photo_base64
            assert call_args["transcript"] == sample_transcript
            assert call_args["language"] == "en"
    
    async def test_enhance_story_with_different_language(self, gemini_service, sample_photo_base64, sample_transcript):
        """Test story enhancement with different language."""
        with patch.object(gemini_service, '_call_gemini_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {
                "enhanced_transcript": "Érase una vez, un valiente caballero...",
                "insights": {"plot": "Mejorado", "character": "Desarrollado"}
            }
            
            result = await gemini_service.enhance_story_with_photo(
                photo_base64=sample_photo_base64,
                transcript=sample_transcript,
                language="es"
            )
            
            assert isinstance(result, GeminiResponse)
            mock_api.assert_called_once()
            call_args = mock_api.call_args[1]
            assert call_args["language"] == "es"
    
    async def test_enhance_story_api_error(self, gemini_service, sample_photo_base64, sample_transcript):
        """Test handling of Gemini API errors."""
        with patch.object(gemini_service, '_call_gemini_api', new_callable=AsyncMock) as mock_api:
            mock_api.side_effect = Exception("API rate limit exceeded")
            
            with pytest.raises(GeminiError, match="Gemini API error"):
                await gemini_service.enhance_story_with_photo(
                    photo_base64=sample_photo_base64,
                    transcript=sample_transcript,
                    language="en"
                )
    
    async def test_enhance_story_invalid_response_format(self, gemini_service, sample_photo_base64, sample_transcript):
        """Test handling of invalid response format from Gemini."""
        with patch.object(gemini_service, '_call_gemini_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"invalid": "format"}  # Missing required fields
            
            with pytest.raises(GeminiError, match="Invalid response format"):
                await gemini_service.enhance_story_with_photo(
                    photo_base64=sample_photo_base64,
                    transcript=sample_transcript,
                    language="en"
                )
    
    def test_validate_inputs_success(self, gemini_service, sample_photo_base64, sample_transcript):
        """Test input validation with valid inputs."""
        # Should not raise any exceptions
        gemini_service._validate_inputs(
            photo_base64=sample_photo_base64,
            transcript=sample_transcript,
            language="en"
        )
    
    def test_validate_inputs_empty_photo(self, gemini_service, sample_transcript):
        """Test input validation with empty photo."""
        with pytest.raises(GeminiError, match="Photo data is required"):
            gemini_service._validate_inputs(
                photo_base64="",
                transcript=sample_transcript,
                language="en"
            )
    
    def test_validate_inputs_empty_transcript(self, gemini_service, sample_photo_base64):
        """Test input validation with empty transcript."""
        with pytest.raises(GeminiError, match="Transcript is required"):
            gemini_service._validate_inputs(
                photo_base64=sample_photo_base64,
                transcript="",
                language="en"
            )
    
    def test_validate_inputs_invalid_language(self, gemini_service, sample_photo_base64, sample_transcript):
        """Test input validation with invalid language code."""
        with pytest.raises(GeminiError, match="Invalid language code"):
            gemini_service._validate_inputs(
                photo_base64=sample_photo_base64,
                transcript=sample_transcript,
                language="invalid"
            )
    
    def test_validate_inputs_transcript_too_long(self, gemini_service, sample_photo_base64):
        """Test input validation with transcript that's too long."""
        long_transcript = "x" * 5001  # Exceeds 5000 char limit
        
        with pytest.raises(GeminiError, match="Transcript too long"):
            gemini_service._validate_inputs(
                photo_base64=sample_photo_base64,
                transcript=long_transcript,
                language="en"
            )
    
    def test_build_prompt_structure(self, gemini_service, sample_photo_base64, sample_transcript):
        """Test that prompt is built with correct structure."""
        prompt = gemini_service._build_prompt(
            transcript=sample_transcript,
            language="en"
        )
        
        # Verify prompt contains key elements
        assert "story enhancement" in prompt.lower()
        assert "analyze the provided photo" in prompt.lower()
        assert sample_transcript in prompt
        assert "enhanced_transcript" in prompt
        assert "insights" in prompt
        assert "plot" in prompt
        assert "character" in prompt
    
    def test_build_prompt_with_different_language(self, gemini_service, sample_transcript):
        """Test prompt building with different language."""
        prompt = gemini_service._build_prompt(
            transcript=sample_transcript,
            language="es"
        )
        
        assert "spanish" in prompt.lower() or "español" in prompt.lower()
        assert sample_transcript in prompt


@pytest.mark.unit  
class TestGeminiResponse:
    """Test GeminiResponse data class."""
    
    def test_gemini_response_creation(self):
        """Test creating GeminiResponse with valid data."""
        response = GeminiResponse(
            enhanced_transcript="Enhanced story",
            insights={
                "plot": "Good plot",
                "character": "Strong character"
            }
        )
        
        assert response.enhanced_transcript == "Enhanced story"
        assert response.insights["plot"] == "Good plot"
        assert response.insights["character"] == "Strong character"
    
    def test_gemini_response_validation(self):
        """Test GeminiResponse validation."""
        # Should not raise with valid data
        GeminiResponse(
            enhanced_transcript="Test story",
            insights={"plot": "test"}
        )
        
        # Test with missing fields would be handled by Pydantic validation


@pytest.mark.unit
class TestGeminiError:
    """Test GeminiError exception class."""
    
    def test_gemini_error_creation(self):
        """Test creating GeminiError with message."""
        error = GeminiError("Test error message")
        assert str(error) == "Test error message"
    
    def test_gemini_error_inheritance(self):
        """Test that GeminiError inherits from Exception."""
        error = GeminiError("Test")
        assert isinstance(error, Exception)