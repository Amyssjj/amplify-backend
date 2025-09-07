"""
Enhancement database model matching OpenAPI specification.
"""
from sqlalchemy import Column, String, Text, DateTime, JSON, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import Base
import enum


class AudioStatusEnum(enum.Enum):
    NOT_GENERATED = "not_generated"
    READY = "ready"


class Enhancement(Base):
    """Enhancement table matching OpenAPI EnhancementDetails schema."""
    __tablename__ = "enhancements"
    
    # Primary key with enh_xxx format
    enhancement_id = Column(String, primary_key=True)
    
    # Foreign key to users table
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    
    # OpenAPI required fields
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    original_transcript = Column(Text, nullable=False)
    enhanced_transcript = Column(Text, nullable=False)
    insights = Column(JSON, nullable=False)  # Dynamic key-value insights
    audio_status = Column(Enum(AudioStatusEnum, values_callable=lambda obj: [e.value for e in obj]), default=AudioStatusEnum.NOT_GENERATED, nullable=False)
    
    # Optional photo data
    photo_base64 = Column(Text, nullable=True)
    
    # Language support
    language = Column(String(2), default="en", nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="enhancements")