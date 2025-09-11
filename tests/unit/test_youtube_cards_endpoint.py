"""
Unit tests for YouTube cards endpoint.
"""
import pytest
from unittest.mock import Mock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from app.core.database import get_db_session
from app.core.auth import get_current_user_optional
from app.models.youtube_card import YouTubeCard


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    mock_db = Mock(spec=Session)
    return mock_db


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    return {"user_id": "user_123", "email": "test@example.com"}


@pytest.fixture
def mock_youtube_cards():
    """Create mock YouTube card data."""
    cards = []

    # First card
    card1 = Mock(spec=YouTubeCard)
    card1.id = "ytc_12345"
    card1.title = "Effective Communication Skills"
    card1.youtube_video_id = "dQw4w9WgXcQ"
    card1.thumbnail_url = "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
    card1.duration_seconds = 180
    card1.start_time_seconds = 30
    card1.end_time_seconds = 210
    card1.clip_transcript = "This is the transcript of the video clip."
    cards.append(card1)

    # Second card
    card2 = Mock(spec=YouTubeCard)
    card2.id = "ytc_12346"
    card2.title = "Leadership Insights"
    card2.youtube_video_id = "abc123def45"
    card2.thumbnail_url = "https://example.com/thumbnail.jpg"
    card2.duration_seconds = 120
    card2.start_time_seconds = None
    card2.end_time_seconds = None
    card2.clip_transcript = "Leadership transcript content."
    cards.append(card2)

    return cards


class TestYouTubeCardsEndpoint:
    """Test suite for YouTube cards endpoint."""

    def test_get_youtube_cards_success(self, mock_db_session, mock_user, mock_youtube_cards):
        """Test successful retrieval of YouTube cards."""
        # Set up mock database query
        mock_query = Mock()
        mock_query.filter_by.return_value.all.return_value = mock_youtube_cards
        mock_db_session.query.return_value = mock_query

        # Override dependencies
        app.dependency_overrides[get_db_session] = lambda: mock_db_session
        app.dependency_overrides[get_current_user_optional] = lambda: mock_user

        # Create test client with overridden dependencies
        with TestClient(app) as client:
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
            assert data[1]["id"] == "ytc_12346"
            assert data[1]["title"] == "Leadership Insights"

        # Clean up overrides
        app.dependency_overrides.clear()

    def test_get_youtube_cards_empty(self, mock_db_session, mock_user):
        """Test retrieval when no YouTube cards are available."""
        # Set up mock database query with empty result
        mock_query = Mock()
        mock_query.filter_by.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query

        # Override dependencies
        app.dependency_overrides[get_db_session] = lambda: mock_db_session
        app.dependency_overrides[get_current_user_optional] = lambda: mock_user

        # Create test client with overridden dependencies
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/youtube-cards",
                headers={"Authorization": "Bearer fake_token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0

        # Clean up overrides
        app.dependency_overrides.clear()

    def test_get_youtube_cards_unauthenticated(self, mock_db_session, mock_youtube_cards):
        """Test that unauthenticated requests still work (returns None user)."""
        # Set up mock database query
        mock_query = Mock()
        mock_query.filter_by.return_value.all.return_value = mock_youtube_cards
        mock_db_session.query.return_value = mock_query

        # Override dependencies - get_current_user_optional returns None for unauthenticated
        app.dependency_overrides[get_db_session] = lambda: mock_db_session
        app.dependency_overrides[get_current_user_optional] = lambda: None

        # Create test client with overridden dependencies
        with TestClient(app) as client:
            response = client.get("/api/v1/youtube-cards")

            # Should still work as endpoint uses get_current_user_optional
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2

        # Clean up overrides
        app.dependency_overrides.clear()

    def test_get_youtube_cards_database_error(self, mock_db_session, mock_user):
        """Test handling of database errors."""
        # Set up mock database to raise an error
        mock_db_session.query.side_effect = Exception("Database connection error")

        # Override dependencies
        app.dependency_overrides[get_db_session] = lambda: mock_db_session
        app.dependency_overrides[get_current_user_optional] = lambda: mock_user

        # Create test client with overridden dependencies
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/youtube-cards",
                headers={"Authorization": "Bearer fake_token"}
            )

            # Should handle the error gracefully
            assert response.status_code == 500
            assert response.json()["detail"] == "Failed to fetch YouTube cards"

        # Clean up overrides
        app.dependency_overrides.clear()
