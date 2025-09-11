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


class PromptType(str, Enum):
    """Type of prompt used for enhancement."""
    PHOTO = "photo"
    YOUTUBE = "youtube"


class EnhancementTextResponse(BaseModel):
    """Response model for Stage 1 - Text enhancement."""
    enhancement_id: str = Field(..., description="Unique ID for the new enhancement", pattern=r"^enh_[a-zA-Z0-9]+$")
    enhanced_transcript: str = Field(..., description="The AI-enhanced version of the story or insight")
    insights: Dict[str, str] = Field(..., description="Dynamic, key-value insights from Gemini analysis")


class EnhancementAudioResponse(BaseModel):
    """Response model for Stage 2 - Audio generation."""
    audio_base64: str = Field(..., description="Base64 encoded MP3 audio data")
    audio_format: str = Field("mp3", description="The format of the audio data")


class EnhancementSummary(BaseModel):
    """Summary model for enhancement history."""
    enhancement_id: str = Field(..., description="Enhancement ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    prompt_type: PromptType = Field(..., description="Type of prompt used for enhancement")
    prompt_title: str = Field(..., description="Title of the prompt")
    prompt_youtube_thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL for YouTube prompts")
    prompt_photo_thumbnail_base64: Optional[str] = Field(None, description="Base64 encoded thumbnail of the photo")
    transcript_preview: str = Field(..., description="A short preview of the enhanced transcript", max_length=100)
    audio_status: AudioStatus = Field(..., description="Audio generation status")
    audio_duration_seconds: Optional[int] = Field(None, description="Duration of generated audio in seconds", ge=0)


class EnhancementDetails(BaseModel):
    """Full enhancement details model."""
    enhancement_id: str = Field(..., description="Enhancement ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    prompt_type: PromptType = Field(..., description="Type of prompt used for enhancement")
    prompt_title: Optional[str] = Field(None, description="Title of the prompt")
    prompt_youtube_thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL for YouTube prompts")
    source_photo_base64: Optional[str] = Field(None, description="Original photo data (only for photo prompts)")
    source_transcript: Optional[str] = Field(None, description="Original YouTube clip transcript (only for YouTube prompts)")
    user_transcript: str = Field(..., description="User's original transcript")
    enhanced_transcript: str = Field(..., description="AI-enhanced transcript")
    insights: Dict[str, str] = Field(..., description="Key-value insights from analysis")
    audio_status: AudioStatus = Field(..., description="Audio availability status")
    audio_duration_seconds: Optional[int] = Field(None, description="Duration of generated audio in seconds", ge=0)


class EnhancementHistoryResponse(BaseModel):
    """Response model for enhancement history."""
    total: int = Field(..., description="Total number of enhancements")
    items: List[EnhancementSummary] = Field(..., description="List of enhancement summaries")
