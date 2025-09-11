"""
Enhancement database model matching OpenAPI specification.
"""
from sqlalchemy import Column, String, Text, DateTime, JSON, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import Base
import enum


class AudioStatusEnum(enum.Enum):
    NOT_GENERATED = "not_generated"
    READY = "ready"


class PromptTypeEnum(enum.Enum):
    PHOTO = "photo"
    YOUTUBE = "youtube"


class Enhancement(Base):
    """Enhancement table matching OpenAPI EnhancementDetails schema."""
    __tablename__ = "enhancements"

    # Primary key with enh_xxx format
    enhancement_id = Column(String, primary_key=True)

    # Foreign key to users table
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)

    # OpenAPI required fields
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Prompt type and metadata
    prompt_type = Column(Enum(PromptTypeEnum, values_callable=lambda obj: [e.value for e in obj]), default=PromptTypeEnum.PHOTO, nullable=False)
    prompt_title = Column(String, nullable=True)
    prompt_youtube_thumbnail_url = Column(String, nullable=True)

    # Source content (photo or YouTube transcript)
    source_photo_base64 = Column(Text, nullable=True)  # Renamed from photo_base64
    source_transcript = Column(Text, nullable=True)  # New field for YouTube source

    # User content
    user_transcript = Column(Text, nullable=False)  # Renamed from original_transcript
    enhanced_transcript = Column(Text, nullable=False)
    insights = Column(JSON, nullable=False)  # Dynamic key-value insights

    # Audio metadata
    audio_status = Column(Enum(AudioStatusEnum, values_callable=lambda obj: [e.value for e in obj]), default=AudioStatusEnum.NOT_GENERATED, nullable=False)
    audio_duration_seconds = Column(Integer, nullable=True)

    # Language support
    language = Column(String(2), default="en", nullable=False)

    # Relationships
    user = relationship("User", back_populates="enhancements")
