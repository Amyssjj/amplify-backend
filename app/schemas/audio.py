"""
Audio-related schemas.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class AudioGenerationRequest(BaseModel):
    """Request model for audio generation."""
    text: str = Field(..., description="Text to convert to audio", min_length=1)
    voice_id: Optional[str] = Field(default=None, description="Voice to use for generation")
    speed: Optional[float] = Field(
        default=1.0, 
        description="Speech speed multiplier",
        ge=0.5,
        le=2.0
    )


class Voice(BaseModel):
    """Voice information."""
    id: str = Field(..., description="Voice identifier")
    name: str = Field(..., description="Voice name")
    language: str = Field(..., description="Language code")
    gender: str = Field(..., description="Voice gender")


class VoicesResponse(BaseModel):
    """Response model for available voices."""
    voices: List[Voice] = Field(..., description="List of available voices")