"""
Shared response models for AI services.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any


class AIResponse(BaseModel):
    """Response model for AI story enhancement."""
    enhanced_transcript: str = Field(
        ..., description="Enhanced version of the original story")
    insights: Dict[str, str] = Field(
        ..., description="Analysis insights about the enhancements made")


# Alias for backward compatibility
GeminiResponse = AIResponse
