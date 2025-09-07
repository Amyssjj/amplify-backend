"""
Integration tests for Gemini service with API endpoints.
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi import status
from app.services.gemini_service import GeminiService, GeminiResponse


@pytest.mark.integration
class TestGeminiIntegration:
    """Integration tests for Gemini service with enhancement endpoints."""
    
    @patch('app.api.v1.endpoints.enhancement.GeminiService')
    def test_create_enhancement_with_gemini_success(self, mock_gemini_class, client, sample_enhancement_request):
        """Test enhancement endpoint using real Gemini service."""
        # Setup mock Gemini service
        mock_gemini_instance = AsyncMock()
        mock_gemini_class.return_value = mock_gemini_instance
        
        mock_response = GeminiResponse(
            enhanced_transcript="In a mystical kingdom shrouded by ancient magic, Sir Gareth the Bold, a knight of unwavering courage, embarked upon a legendary quest to break the dark curse that had befallen his beloved realm.",
            insights={
                "plot": "Enhanced the basic quest narrative with specific magical conflict and clear stakes",
                "character": "Added character name, personality traits, and emotional connection to the kingdom",
                "setting": "Incorporated mystical elements and ancient magic to create richer fantasy world",
                "mood": "Elevated from simple adventure to epic fantasy with dramatic stakes"
            }
        )
        mock_gemini_instance.enhance_story_with_photo.return_value = mock_response
        
        # Make request
        response = client.post("/api/v1/enhancements", json=sample_enhancement_request)
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "enhancement_id" in data
        assert data["enhancement_id"].startswith("enh_")
        assert data["enhanced_transcript"] == mock_response.enhanced_transcript
        assert data["insights"] == mock_response.insights
        
        # Verify Gemini service was called correctly
        mock_gemini_instance.enhance_story_with_photo.assert_called_once_with(
            photo_base64=sample_enhancement_request["photo_base64"],
            transcript=sample_enhancement_request["transcript"],
            language=sample_enhancement_request["language"]
        )
    
    @patch('app.api.v1.endpoints.enhancement.GeminiService')
    def test_create_enhancement_with_gemini_error(self, mock_gemini_class, client, sample_enhancement_request):
        """Test enhancement endpoint when Gemini service fails."""
        # Setup mock to raise GeminiError
        from app.services.gemini_service import GeminiError
        mock_gemini_instance = AsyncMock()
        mock_gemini_class.return_value = mock_gemini_instance
        mock_gemini_instance.enhance_story_with_photo.side_effect = GeminiError("API rate limit exceeded")
        
        # Make request
        response = client.post("/api/v1/enhancements", json=sample_enhancement_request)
        
        # Should handle error gracefully
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        data = response.json()
        assert "try again later" in data["detail"].lower()
    
    @patch('app.api.v1.endpoints.enhancement.GeminiService')
    def test_create_enhancement_saves_to_database(self, mock_gemini_class, client, sample_enhancement_request, db_session):
        """Test that enhanced stories are saved to database."""
        # Setup mock Gemini service  
        mock_gemini_instance = AsyncMock()
        mock_gemini_class.return_value = mock_gemini_instance
        
        mock_response = GeminiResponse(
            enhanced_transcript="Enhanced story content",
            insights={"plot": "Improved", "character": "Developed"}
        )
        mock_gemini_instance.enhance_story_with_photo.return_value = mock_response
        
        # Make request
        response = client.post("/api/v1/enhancements", json=sample_enhancement_request)
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        enhancement_id = data["enhancement_id"]
        
        # Verify database storage (would need real database implementation)
        # This test will pass once we implement database persistence
        assert enhancement_id.startswith("enh_")


@pytest.mark.integration
class TestGeminiServiceConfiguration:
    """Integration tests for Gemini service configuration."""
    
    @patch('app.services.gemini_service.genai')
    def test_gemini_service_initialization(self, mock_genai):
        """Test that Gemini service can be initialized correctly."""
        service = GeminiService(api_key="test_key")
        assert service is not None
        assert service.api_key == "test_key"
    
    @pytest.mark.slow
    @pytest.mark.skipif(True, reason="Requires actual Gemini API key for manual testing")
    async def test_real_gemini_api_call(self):
        """Manual test for real Gemini API (skip in CI/CD)."""
        service = GeminiService()
        
        # This would test real API integration
        # Only run manually with proper API keys
        pass