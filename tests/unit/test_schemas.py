"""
Unit tests for Pydantic schemas.
"""
import pytest
from pydantic import ValidationError
from app.schemas.enhancement import (
    EnhancementRequest, EnhancementTextResponse, EnhancementAudioResponse,
    EnhancementSummary, EnhancementDetails, EnhancementHistoryResponse,
    AudioStatus
)
from app.schemas.auth import GoogleAuthRequest, UserProfile, AuthResponse
import base64


@pytest.mark.unit
class TestEnhancementSchemas:
    """Test Enhancement-related schemas."""
    
    def test_enhancement_request_valid(self, sample_enhancement_request):
        """Test valid EnhancementRequest creation."""
        request = EnhancementRequest(**sample_enhancement_request)
        
        assert request.transcript == "Once upon a time, there was a brave knight who embarked on a quest to save the kingdom."
        assert request.language == "en"
        assert len(request.photo_base64) > 0
    
    def test_enhancement_request_validation_errors(self):
        """Test EnhancementRequest validation errors."""
        # Missing required fields
        with pytest.raises(ValidationError) as exc_info:
            EnhancementRequest()
        
        errors = exc_info.value.errors()
        field_names = [error["loc"][0] for error in errors]
        assert "photo_base64" in field_names
        assert "transcript" in field_names
        
        # Invalid language code
        with pytest.raises(ValidationError):
            EnhancementRequest(
                photo_base64="fake_base64",
                transcript="Test story",
                language="invalid"  # Should be 2 characters
            )
        
        # Transcript too long
        with pytest.raises(ValidationError):
            EnhancementRequest(
                photo_base64="fake_base64",
                transcript="x" * 5001,  # Exceeds 5000 char limit
                language="en"
            )
        
        # Empty transcript
        with pytest.raises(ValidationError):
            EnhancementRequest(
                photo_base64="fake_base64",
                transcript="",  # Empty string
                language="en"
            )
    
    def test_enhancement_text_response_valid(self):
        """Test valid EnhancementTextResponse creation."""
        response = EnhancementTextResponse(
            enhancement_id="enh_abc123",
            enhanced_transcript="This is an enhanced story with better plot development.",
            insights={"plot": "Good structure", "character": "Well developed"}
        )
        
        assert response.enhancement_id == "enh_abc123"
        assert "enhanced story" in response.enhanced_transcript
        assert response.insights["plot"] == "Good structure"
    
    def test_enhancement_text_response_validation(self):
        """Test EnhancementTextResponse validation."""
        # Invalid enhancement_id format
        with pytest.raises(ValidationError):
            EnhancementTextResponse(
                enhancement_id="invalid_id",  # Should match pattern ^enh_[a-zA-Z0-9]+$
                enhanced_transcript="Test",
                insights={}
            )
    
    def test_enhancement_audio_response(self):
        """Test EnhancementAudioResponse schema."""
        response = EnhancementAudioResponse(
            audio_base64="UklGRnoGAABXQVZFZm10IBAAAAABAAEA...",
            audio_format="mp3"
        )
        
        assert response.audio_format == "mp3"
        assert len(response.audio_base64) > 0
    
    def test_audio_status_enum(self):
        """Test AudioStatus enum."""
        assert AudioStatus.NOT_GENERATED == "not_generated"
        assert AudioStatus.READY == "ready"
        
        # Test in schema
        summary = EnhancementSummary(
            enhancement_id="enh_test123",
            created_at="2025-09-07T12:00:00Z",
            transcript_preview="Once upon a time...",
            audio_status=AudioStatus.READY
        )
        
        assert summary.audio_status == "ready"
    
    def test_enhancement_details_schema(self):
        """Test EnhancementDetails schema."""
        details = EnhancementDetails(
            enhancement_id="enh_test123",
            created_at="2025-09-07T12:00:00Z",
            original_transcript="Original story",
            enhanced_transcript="Enhanced story",
            insights={"plot": "Good", "character": "Strong"},
            audio_status=AudioStatus.NOT_GENERATED,
            photo_base64=None
        )
        
        assert details.enhancement_id == "enh_test123"
        assert details.audio_status == "not_generated"
        assert details.photo_base64 is None
    
    def test_enhancement_history_response(self):
        """Test EnhancementHistoryResponse schema."""
        history = EnhancementHistoryResponse(
            total=5,
            items=[
                EnhancementSummary(
                    enhancement_id="enh_test1",
                    created_at="2025-09-07T12:00:00Z",
                    transcript_preview="Story 1...",
                    audio_status=AudioStatus.READY
                ),
                EnhancementSummary(
                    enhancement_id="enh_test2", 
                    created_at="2025-09-07T13:00:00Z",
                    transcript_preview="Story 2...",
                    audio_status=AudioStatus.NOT_GENERATED
                )
            ]
        )
        
        assert history.total == 5
        assert len(history.items) == 2
        assert history.items[0].enhancement_id == "enh_test1"


@pytest.mark.unit
class TestAuthSchemas:
    """Test Authentication-related schemas."""
    
    def test_google_auth_request(self, sample_google_auth_request):
        """Test GoogleAuthRequest schema."""
        request = GoogleAuthRequest(**sample_google_auth_request)
        
        assert request.id_token == "fake_google_id_token_for_testing"
    
    def test_google_auth_request_validation(self):
        """Test GoogleAuthRequest validation."""
        with pytest.raises(ValidationError):
            GoogleAuthRequest()  # Missing id_token
    
    def test_user_profile_schema(self, sample_user_data):
        """Test UserProfile schema."""
        # Remove fields not in UserProfile
        profile_data = {
            "user_id": sample_user_data["user_id"],
            "email": sample_user_data["email"],
            "name": sample_user_data["name"],
            "picture": sample_user_data["picture"]
        }
        
        profile = UserProfile(**profile_data)
        
        assert profile.user_id == "usr_test123"
        assert profile.email == "test@example.com"
        assert profile.name == "Test User"
        assert profile.picture == "https://example.com/avatar.jpg"
    
    def test_user_profile_optional_fields(self):
        """Test UserProfile with optional fields."""
        profile = UserProfile(
            user_id="usr_test456",
            email="test2@example.com"
        )
        
        assert profile.user_id == "usr_test456"
        assert profile.email == "test2@example.com"
        assert profile.name is None
        assert profile.picture is None
    
    def test_auth_response_schema(self, sample_user_data):
        """Test AuthResponse schema."""
        profile_data = {
            "user_id": sample_user_data["user_id"],
            "email": sample_user_data["email"],
            "name": sample_user_data["name"],
            "picture": sample_user_data["picture"]
        }
        
        auth_response = AuthResponse(
            access_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            user=UserProfile(**profile_data)
        )
        
        assert auth_response.access_token.startswith("eyJ")
        assert auth_response.token_type == "bearer"
        assert auth_response.expires_in == 3600
        assert auth_response.user.email == "test@example.com"
    
    def test_auth_response_validation(self):
        """Test AuthResponse validation."""
        with pytest.raises(ValidationError):
            AuthResponse(
                access_token="token123"
                # Missing required 'user' field
            )