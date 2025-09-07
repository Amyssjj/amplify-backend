"""
Enhancement-related schemas matching OpenAPI specification.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum


class AudioStatus(str, Enum):
    """Audio generation status."""
    NOT_GENERATED = "not_generated"
    READY = "ready"


class EnhancementRequest(BaseModel):
    """Request model for enhancement creation (OpenAPI EnhancementRequest)."""
    photo_base64: str = Field(..., description="Base64 encoded JPEG or PNG image (max 10MB)")
    transcript: str = Field(..., description="User's original story transcript", min_length=1, max_length=5000)
    language: str = Field(default="en", description="Language code (ISO 639-1)", pattern=r"^[a-z]{2}$")


class EnhancementTextResponse(BaseModel):
    """Response model for Stage 1 - Text enhancement."""
    enhancement_id: str = Field(..., description="Unique ID for the new enhancement", pattern=r"^enh_[a-zA-Z0-9]+$")
    enhanced_transcript: str = Field(..., description="The AI-enhanced version of the story")
    insights: Dict[str, str] = Field(..., description="Dynamic, key-value insights from Gemini analysis")


class EnhancementAudioResponse(BaseModel):
    """Response model for Stage 2 - Audio generation."""
    audio_base64: str = Field(..., description="Base64 encoded MP3 audio data")
    audio_format: str = Field("mp3", description="The format of the audio data")


class EnhancementSummary(BaseModel):
    """Summary model for enhancement history."""
    enhancement_id: str = Field(..., description="Enhancement ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    transcript_preview: str = Field(..., description="A short preview of the enhanced transcript", max_length=100)
    audio_status: AudioStatus = Field(..., description="Audio generation status")


class EnhancementDetails(BaseModel):
    """Full enhancement details model."""
    enhancement_id: str = Field(..., description="Enhancement ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    original_transcript: str = Field(..., description="Original user transcript")
    enhanced_transcript: str = Field(..., description="AI-enhanced transcript")
    insights: Dict[str, str] = Field(..., description="Key-value insights from analysis")
    audio_status: AudioStatus = Field(..., description="Audio availability status")
    photo_base64: Optional[str] = Field(None, description="Original photo data for display")


class EnhancementHistoryResponse(BaseModel):
    """Response model for enhancement history."""
    total: int = Field(..., description="Total number of enhancements")
    items: List[EnhancementSummary] = Field(..., description="List of enhancement summaries")