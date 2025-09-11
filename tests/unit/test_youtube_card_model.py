"""
Unit tests for YouTubeCard database model.
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.youtube_card import YouTubeCard
from app.core.database import Base


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


class TestYouTubeCardModel:
    """Test suite for YouTubeCard model."""

    def test_create_youtube_card(self, db_session):
        """Test creating a YouTubeCard instance."""
        card = YouTubeCard(
            id="ytc_12345",
            title="Effective Communication Skills",
            youtube_video_id="dQw4w9WgXcQ",
            thumbnail_url="https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
            duration_seconds=180,
            start_time_seconds=30,
            end_time_seconds=210,
            clip_transcript="This is the transcript of the video clip.",
            is_active=True
        )

        db_session.add(card)
        db_session.commit()

        # Retrieve and verify
        saved_card = db_session.query(YouTubeCard).filter_by(id="ytc_12345").first()
        assert saved_card is not None
        assert saved_card.title == "Effective Communication Skills"
        assert saved_card.youtube_video_id == "dQw4w9WgXcQ"
        assert saved_card.duration_seconds == 180
        assert saved_card.is_active is True

    def test_youtube_card_nullable_fields(self, db_session):
        """Test that start_time and end_time can be null."""
        card = YouTubeCard(
            id="ytc_12346",
            title="Leadership Insights",
            youtube_video_id="abc123def45",
            thumbnail_url="https://example.com/thumbnail.jpg",
            duration_seconds=120,
            start_time_seconds=None,  # Nullable
            end_time_seconds=None,     # Nullable
            clip_transcript="Leadership transcript content.",
            is_active=True
        )

        db_session.add(card)
        db_session.commit()

        saved_card = db_session.query(YouTubeCard).filter_by(id="ytc_12346").first()
        assert saved_card.start_time_seconds is None
        assert saved_card.end_time_seconds is None

    def test_youtube_card_timestamps(self, db_session):
        """Test that created_at and updated_at are automatically set."""
        card = YouTubeCard(
            id="ytc_12347",
            title="Public Speaking Tips",
            youtube_video_id="xyz789abc12",
            thumbnail_url="https://example.com/thumb2.jpg",
            duration_seconds=90,
            clip_transcript="Public speaking tips transcript.",
            is_active=True
        )

        db_session.add(card)
        db_session.commit()

        saved_card = db_session.query(YouTubeCard).filter_by(id="ytc_12347").first()
        assert saved_card.created_at is not None
        assert isinstance(saved_card.created_at, datetime)
        assert saved_card.updated_at is not None
        assert isinstance(saved_card.updated_at, datetime)

    def test_get_active_cards(self, db_session):
        """Test filtering active YouTube cards."""
        # Create active and inactive cards
        active_card = YouTubeCard(
            id="ytc_active",
            title="Active Card",
            youtube_video_id="active12345",
            thumbnail_url="https://example.com/active.jpg",
            duration_seconds=60,
            clip_transcript="Active card transcript.",
            is_active=True
        )

        inactive_card = YouTubeCard(
            id="ytc_inactive",
            title="Inactive Card",
            youtube_video_id="inactive123",
            thumbnail_url="https://example.com/inactive.jpg",
            duration_seconds=60,
            clip_transcript="Inactive card transcript.",
            is_active=False
        )

        db_session.add_all([active_card, inactive_card])
        db_session.commit()

        # Query only active cards
        active_cards = db_session.query(YouTubeCard).filter_by(is_active=True).all()
        assert len(active_cards) == 1
        assert active_cards[0].id == "ytc_active"
