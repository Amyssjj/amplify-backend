"""
Unit tests for YouTube-related Pydantic schemas.
"""
import pytest
from pydantic import ValidationError

from app.schemas.youtube import YouTubeCard, YouTubeEnhancementRequest, PhotoEnhancementRequest, EnhancementRequest


class TestYouTubeCardSchema:
    """Test suite for YouTubeCard Pydantic schema."""

    def test_valid_youtube_card(self):
        """Test creating a valid YouTubeCard schema."""
        card_data = {
            "id": "ytc_12345",
            "title": "Effective Communication Skills",
            "youtube_video_id": "dQw4w9WgXcQ",
            "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
            "duration_seconds": 180,
            "start_time_seconds": 30,
            "end_time_seconds": 210,
            "clip_transcript": "This is the transcript of the video clip."
        }

        card = YouTubeCard(**card_data)
        assert card.id == "ytc_12345"
        assert card.title == "Effective Communication Skills"
        assert card.youtube_video_id == "dQw4w9WgXcQ"
        assert card.duration_seconds == 180

    def test_youtube_card_without_optional_fields(self):
        """Test YouTubeCard with nullable start/end times."""
        card_data = {
            "id": "ytc_12346",
            "title": "Leadership Insights",
            "youtube_video_id": "abc123def45",
            "thumbnail_url": "https://example.com/thumbnail.jpg",
            "duration_seconds": 120,
            "clip_transcript": "Leadership transcript content."
        }

        card = YouTubeCard(**card_data)
        assert card.start_time_seconds is None
        assert card.end_time_seconds is None

    def test_youtube_card_invalid_video_id(self):
        """Test that invalid YouTube video ID fails validation."""
        card_data = {
            "id": "ytc_12347",
            "title": "Test Video",
            "youtube_video_id": "invalid",  # Should be 11 characters
            "thumbnail_url": "https://example.com/thumb.jpg",
            "duration_seconds": 60,
            "clip_transcript": "Test transcript."
        }

        with pytest.raises(ValidationError) as exc_info:
            YouTubeCard(**card_data)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("youtube_video_id",) for error in errors)

    def test_youtube_card_negative_duration(self):
        """Test that negative duration fails validation."""
        card_data = {
            "id": "ytc_12348",
            "title": "Test Video",
            "youtube_video_id": "12345678901",
            "thumbnail_url": "https://example.com/thumb.jpg",
            "duration_seconds": -1,  # Invalid negative duration
            "clip_transcript": "Test transcript."
        }

        with pytest.raises(ValidationError) as exc_info:
            YouTubeCard(**card_data)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("duration_seconds",) for error in errors)


class TestEnhancementRequestSchemas:
    """Test suite for discriminated enhancement request schemas."""

    def test_photo_enhancement_request(self):
        """Test creating a PhotoEnhancementRequest."""
        request_data = {
            "type": "photo",
            "photo_base64": "base64encodedphotodata",
            "transcript": "This is my story about the photo.",
            "language": "en"
        }

        request = PhotoEnhancementRequest(**request_data)
        assert request.type == "photo"
        assert request.photo_base64 == "base64encodedphotodata"
        assert request.transcript == "This is my story about the photo."

    def test_youtube_enhancement_request(self):
        """Test creating a YouTubeEnhancementRequest."""
        request_data = {
            "type": "youtube",
            "source_transcript": "Original video transcript content.",
            "transcript": "My summary of the video.",
            "language": "en"
        }

        request = YouTubeEnhancementRequest(**request_data)
        assert request.type == "youtube"
        assert request.source_transcript == "Original video transcript content."
        assert request.transcript == "My summary of the video."

    def test_enhancement_request_discriminator(self):
        """Test that EnhancementRequest properly discriminates based on type."""
        # Test photo type
        photo_data = {
            "type": "photo",
            "photo_base64": "photodata",
            "transcript": "Photo story"
        }
        request = EnhancementRequest(**photo_data)
        assert isinstance(request, PhotoEnhancementRequest)

        # Test youtube type
        youtube_data = {
            "type": "youtube",
            "source_transcript": "Video transcript",
            "transcript": "My summary"
        }
        request = EnhancementRequest(**youtube_data)
        assert isinstance(request, YouTubeEnhancementRequest)

    def test_invalid_enhancement_type(self):
        """Test that invalid type fails validation."""
        invalid_data = {
            "type": "invalid_type",
            "transcript": "Some transcript"
        }

        with pytest.raises(ValidationError):
            EnhancementRequest(**invalid_data)

    def test_photo_request_missing_photo(self):
        """Test that photo request without photo_base64 fails."""
        invalid_data = {
            "type": "photo",
            "transcript": "Photo story without photo"
        }

        with pytest.raises(ValidationError) as exc_info:
            PhotoEnhancementRequest(**invalid_data)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("photo_base64",) for error in errors)

    def test_youtube_request_missing_source(self):
        """Test that youtube request without source_transcript fails."""
        invalid_data = {
            "type": "youtube",
            "transcript": "My summary without source"
        }

        with pytest.raises(ValidationError) as exc_info:
            YouTubeEnhancementRequest(**invalid_data)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("source_transcript",) for error in errors)
