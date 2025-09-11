"""
YouTubeCard database model.
"""
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class YouTubeCard(Base):
    """Model for YouTube practice cards."""

    __tablename__ = "youtube_cards"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    youtube_video_id = Column(String(11), nullable=False)
    thumbnail_url = Column(String, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    start_time_seconds = Column(Integer, nullable=True)
    end_time_seconds = Column(Integer, nullable=True)
    clip_transcript = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)
