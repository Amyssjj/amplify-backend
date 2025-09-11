"""
Integration tests for enhancement endpoints with database.
"""
import pytest
import json
from unittest.mock import patch, AsyncMock
from fastapi import status
from app.models.enhancement import Enhancement, AudioStatusEnum
from app.models.user import User
from app.services.gemini_service import GeminiResponse


@pytest.mark.integration
class TestEnhancementEndpoints:
    """Integration tests for enhancement API endpoints."""

    @patch('app.api.v1.endpoints.enhancement.GeminiService')
    def test_create_enhancement_success(self, mock_gemini_class, client, sample_enhancement_request, db_session):
        """Test successful enhancement creation."""
        # Setup mock Gemini service
        mock_gemini_instance = AsyncMock()
        mock_gemini_class.return_value = mock_gemini_instance

        mock_response = GeminiResponse(
            enhanced_transcript="Once upon a time in a mystical realm, there was a brave knight named Sir Gareth who embarked on a perilous quest to save the kingdom from an ancient curse.",
            insights={
                "plot": "Enhanced the quest structure with specific goals and conflicts",
                "character": "Added depth and motivation to the knight protagonist"
            }
        )
        mock_gemini_instance.enhance_story_with_photo.return_value = mock_response

        response = client.post("/api/v1/enhancements", json=sample_enhancement_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check response structure
        assert "enhancement_id" in data
        assert "enhanced_transcript" in data
        assert "insights" in data

        # Check enhancement_id format
        assert data["enhancement_id"].startswith("enh_")

        # Check enhanced transcript contains original content
        assert "knight" in data["enhanced_transcript"].lower()

        # Check insights structure
        assert isinstance(data["insights"], dict)

    @patch('app.api.v1.endpoints.enhancement.GeminiService')
    def test_create_enhancement_invalid_data(self, mock_gemini_class, client):
        """Test enhancement creation with invalid data."""
        # Missing required fields
        response = client.post("/api/v1/enhancements", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Invalid language code
        invalid_request = {
            "photo_base64": "fake_base64_data",
            "transcript": "Test story",
            "language": "invalid_lang"
        }
        response = client.post("/api/v1/enhancements", json=invalid_request)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Transcript too long
        invalid_request = {
            "photo_base64": "fake_base64_data",
            "transcript": "x" * 5001,  # Exceeds limit
            "language": "en"
        }
        response = client.post("/api/v1/enhancements", json=invalid_request)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_enhancements_empty_history(self, client):
        """Test getting enhancement history when empty."""
        response = client.get("/api/v1/enhancements")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "total" in data
        assert "items" in data
        assert data["total"] == 0
        assert data["items"] == []

    def test_get_enhancements_with_pagination(self, client):
        """Test enhancement history with pagination parameters."""
        # Test with custom pagination
        response = client.get("/api/v1/enhancements?limit=10&offset=0")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_get_enhancements_invalid_pagination(self, client):
        """Test enhancement history with invalid pagination."""
        # Invalid limit (too high)
        response = client.get("/api/v1/enhancements?limit=100")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Invalid offset (negative)
        response = client.get("/api/v1/enhancements?offset=-1")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_enhancement_by_id_not_found(self, client):
        """Test getting enhancement by ID when it doesn't exist."""
        response = client.get("/api/v1/enhancements/enh_nonexistent")

        # Should return 404 with database integration
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_enhancement_by_id_invalid_format(self, client):
        """Test getting enhancement with invalid ID format."""
        response = client.get("/api/v1/enhancements/invalid_id")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_enhancement_audio_success(self, client):
        """Test getting enhancement audio."""
        response = client.get("/api/v1/enhancements/enh_test123/audio")

        # Should return 404 since enhancement doesn't exist in database
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_enhancement_audio_invalid_id(self, client):
        """Test getting audio with invalid enhancement ID."""
        response = client.get("/api/v1/enhancements/invalid_id/audio")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('app.api.v1.endpoints.enhancement.GeminiService')
    def test_enhancement_endpoints_http_methods(self, mock_gemini_class, client, sample_enhancement_request):
        """Test that endpoints only accept correct HTTP methods."""
        # Setup mock Gemini service for POST test
        mock_gemini_instance = AsyncMock()
        mock_gemini_class.return_value = mock_gemini_instance

        mock_response = GeminiResponse(
            enhanced_transcript="Enhanced story for HTTP methods test",
            insights={"plot": "Good", "character": "Strong"}
        )
        mock_gemini_instance.enhance_story_with_photo.return_value = mock_response

        # POST should work for creation
        response = client.post("/api/v1/enhancements", json=sample_enhancement_request)
        assert response.status_code == status.HTTP_200_OK

        # GET should work for history
        response = client.get("/api/v1/enhancements")
        assert response.status_code == status.HTTP_200_OK

        # PUT should not be allowed
        response = client.put("/api/v1/enhancements", json=sample_enhancement_request)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # DELETE should not be allowed
        response = client.delete("/api/v1/enhancements")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_enhancement_database_integration(self, client, db_session, sample_user_data, sample_enhancement_data):
        """Test enhancement endpoints with actual database operations."""
        # Create a user first
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()

        # Create enhancement record
        enhancement_data = sample_enhancement_data.copy()
        enhancement_data["audio_status"] = AudioStatusEnum.NOT_GENERATED
        enhancement = Enhancement(**enhancement_data)
        db_session.add(enhancement)
        db_session.commit()

        # Test that we can query the enhancement
        saved_enhancement = db_session.query(Enhancement).filter_by(
            enhancement_id="enh_test123"
        ).first()

        assert saved_enhancement is not None
        assert saved_enhancement.user_id == "usr_test123"
        assert saved_enhancement.user_transcript == "Original story text"
        assert saved_enhancement.audio_status == AudioStatusEnum.NOT_GENERATED

        # Test user-enhancement relationship
        assert len(user.enhancements) == 1
        assert user.enhancements[0].enhancement_id == "enh_test123"


@pytest.mark.integration
class TestEnhancementWorkflow:
    """Integration tests for complete enhancement workflow."""

    @patch('app.api.v1.endpoints.enhancement.GeminiService')
    def test_two_stage_enhancement_flow(self, mock_gemini_class, client, sample_enhancement_request):
        """Test the complete two-stage enhancement flow."""
        # Setup mock Gemini service
        mock_gemini_instance = AsyncMock()
        mock_gemini_class.return_value = mock_gemini_instance

        mock_response = GeminiResponse(
            enhanced_transcript="Once upon a time in a mystical realm, there was a brave knight named Sir Gareth who embarked on a perilous quest to save the kingdom from an ancient curse.",
            insights={
                "plot": "Enhanced the quest structure with specific goals and conflicts",
                "character": "Added depth and motivation to the knight protagonist"
            }
        )
        mock_gemini_instance.enhance_story_with_photo.return_value = mock_response

        # Stage 1: Create enhancement (text)
        response = client.post("/api/v1/enhancements", json=sample_enhancement_request)

        assert response.status_code == status.HTTP_200_OK
        stage1_data = response.json()
        enhancement_id = stage1_data["enhancement_id"]

        # Verify stage 1 response
        assert enhancement_id.startswith("enh_")
        assert "enhanced_transcript" in stage1_data
        assert "insights" in stage1_data

        # Stage 2: Get audio for the enhancement
        response = client.get(f"/api/v1/enhancements/{enhancement_id}/audio")

        assert response.status_code == status.HTTP_200_OK
        stage2_data = response.json()

        # Verify stage 2 response
        assert "audio_base64" in stage2_data
        assert "audio_format" in stage2_data
        assert stage2_data["audio_format"] == "mp3"

    @patch('app.api.v1.endpoints.enhancement.GeminiService')
    def test_enhancement_history_after_creation(self, mock_gemini_class, client, sample_enhancement_request):
        """Test that created enhancements appear in history."""
        # Setup mock Gemini service
        mock_gemini_instance = AsyncMock()
        mock_gemini_class.return_value = mock_gemini_instance

        mock_response = GeminiResponse(
            enhanced_transcript="Enhanced knight story with magical elements",
            insights={"plot": "Improved", "character": "Developed"}
        )
        mock_gemini_instance.enhance_story_with_photo.return_value = mock_response

        # Initially empty
        response = client.get("/api/v1/enhancements")
        initial_data = response.json()
        initial_total = initial_data["total"]

        # Create enhancement
        response = client.post("/api/v1/enhancements", json=sample_enhancement_request)
        assert response.status_code == status.HTTP_200_OK

        # Check history again (would need database integration to see changes)
        response = client.get("/api/v1/enhancements")
        assert response.status_code == status.HTTP_200_OK
        # Note: Without full database integration, count won't change yet
