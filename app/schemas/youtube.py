"""
YouTube-related schemas matching OpenAPI specification.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, Union
from typing_extensions import Annotated


class YouTubeCard(BaseModel):
    """Schema for YouTube practice cards (OpenAPI YouTubeCard)."""
    id: str = Field(..., description="Unique identifier for the YouTube card", example="ytc_12345")
    title: str = Field(..., description="Title of the video clip")
    youtube_video_id: str = Field(..., description="The 11-character YouTube video ID", pattern=r"^[a-zA-Z0-9_-]{11}$")
    thumbnail_url: str = Field(..., description="Direct URL to the video thumbnail image")
    duration_seconds: int = Field(..., description="Duration of the video clip in seconds", ge=1)
    start_time_seconds: Optional[int] = Field(None, description="Optional start time for the clip in seconds", ge=0)
    end_time_seconds: Optional[int] = Field(None, description="Optional end time for the clip in seconds", ge=0)
    clip_transcript: str = Field(..., description="Transcript corresponding to the clip's duration")

    @field_validator('youtube_video_id')
    @classmethod
    def validate_youtube_id(cls, v: str) -> str:
        """Validate YouTube video ID format."""
        if len(v) != 11:
            raise ValueError("YouTube video ID must be exactly 11 characters")
        return v


class PhotoEnhancementRequest(BaseModel):
    """Request model for photo-based enhancement (OpenAPI PhotoEnhancementRequest)."""
    type: Literal["photo"] = Field(..., description="Type of enhancement prompt")
    photo_base64: str = Field(..., description="Base64 encoded JPEG or PNG image (max 10MB)")
    transcript: str = Field(..., description="User's original story transcript", min_length=1, max_length=5000)
    language: str = Field(default="en", description="Language code (ISO 639-1)", pattern=r"^[a-z]{2}$")


class YouTubeEnhancementRequest(BaseModel):
    """Request model for YouTube-based enhancement (OpenAPI YouTubeEnhancementRequest)."""
    type: Literal["youtube"] = Field(..., description="Type of enhancement prompt")
    source_transcript: str = Field(..., description="Original transcript from the YouTube video clip", min_length=1)
    transcript: str = Field(..., description="User's summary or takeaway transcript", min_length=1, max_length=5000)
    language: str = Field(default="en", description="Language code (ISO 639-1)", pattern=r"^[a-z]{2}$")


# Discriminated union for enhancement requests
EnhancementRequest = Annotated[
    Union[PhotoEnhancementRequest, YouTubeEnhancementRequest],
    Field(discriminator='type')
]
