"""
Unit tests for YouTube cards endpoint.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.youtube_cards import router
from app.models.youtube_card import YouTubeCard
from app.core.auth import get_current_user


# Create a test app with just the YouTube cards router
from fastapi import FastAPI
test_app = FastAPI()
test_app.include_router(router, prefix="/api/v1")


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(test_app)


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    return {"user_id": "user_123", "email": "test@example.com"}


@pytest.fixture
def mock_youtube_cards():
    """Create mock YouTube card data."""
    return [
        {
            "id": "ytc_12345",
            "title": "Effective Communication Skills",
            "youtube_video_id": "dQw4w9WgXcQ",
            "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
            "duration_seconds": 180,
            "start_time_seconds": 30,
            "end_time_seconds": 210,
            "clip_transcript": "This is the transcript of the video clip."
        },
        {
            "id": "ytc_12346",
            "title": "Leadership Insights",
            "youtube_video_id": "abc123def45",
            "thumbnail_url": "https://example.com/thumbnail.jpg",
            "duration_seconds": 120,
            "start_time_seconds": None,
            "end_time_seconds": None,
            "clip_transcript": "Leadership transcript content."
        }
    ]


class TestYouTubeCardsEndpoint:
    """Test suite for YouTube cards endpoint."""

    def test_get_youtube_cards_success(self, client, mock_user, mock_youtube_cards):
        """Test successful retrieval of YouTube cards."""
        with patch("app.api.v1.youtube_cards.get_current_user", return_value=mock_user):
            with patch("app.api.v1.youtube_cards.get_db") as mock_get_db:
                # Setup mock database session
                mock_db = Mock(spec=Session)
                mock_get_db.return_value = mock_db

                # Create mock YouTubeCard objects
                mock_card_objects = [
                    YouTubeCard(**card_data) for card_data in mock_youtube_cards
                ]

                # Mock the query
                mock_query = Mock()
                mock_query.filter_by.return_value.all.return_value = mock_card_objects
                mock_db.query.return_value = mock_query

                # Make request
                response = client.get(
                    "/api/v1/youtube-cards",
                    headers={"Authorization": "Bearer fake_token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
                assert len(data) == 2
                assert data[0]["id"] == "ytc_12345"
                assert data[0]["title"] == "Effective Communication Skills"

    def test_get_youtube_cards_empty(self, client, mock_user):
        """Test retrieval when no YouTube cards are available."""
        with patch("app.api.v1.youtube_cards.get_current_user", return_value=mock_user):
            with patch("app.api.v1.youtube_cards.get_db") as mock_get_db:
                # Setup mock database session
                mock_db = Mock(spec=Session)
                mock_get_db.return_value = mock_db

                # Mock empty query result
                mock_query = Mock()
                mock_query.filter_by.return_value.all.return_value = []
                mock_db.query.return_value = mock_query

                # Make request
                response = client.get(
                    "/api/v1/youtube-cards",
                    headers={"Authorization": "Bearer fake_token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
                assert len(data) == 0

    def test_get_youtube_cards_unauthorized(self, client):
        """Test that unauthorized requests are rejected."""
        with patch("app.api.v1.youtube_cards.get_current_user", side_effect=Exception("Unauthorized")):
            response = client.get("/api/v1/youtube-cards")
            assert response.status_code == 401 or response.status_code == 403

    def test_get_youtube_cards_database_error(self, client, mock_user):
        """Test handling of database errors."""
        with patch("app.api.v1.youtube_cards.get_current_user", return_value=mock_user):
            with patch("app.api.v1.youtube_cards.get_db") as mock_get_db:
                # Setup mock database session that raises an error
                mock_db = Mock(spec=Session)
                mock_db.query.side_effect = Exception("Database error")
                mock_get_db.return_value = mock_db

                # Make request
                response = client.get(
                    "/api/v1/youtube-cards",
                    headers={"Authorization": "Bearer fake_token"}
                )

                # Should handle the error gracefully
                assert response.status_code == 500
