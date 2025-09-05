"""
Enhancement-related schemas.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class EnhancementType(str, Enum):
    """Types of story enhancement."""
    PLOT = "plot"
    CHARACTER = "character"
    DIALOGUE = "dialogue"
    SETTING = "setting"


class EnhancementRequest(BaseModel):
    """Request model for story enhancement."""
    story_text: str = Field(..., description="The story text to enhance", min_length=1)
    enhancement_type: Optional[EnhancementType] = Field(
        default=None, description="Type of enhancement requested"
    )


class Insight(BaseModel):
    """Individual insight about the story."""
    type: str = Field(..., description="Type of insight")
    description: str = Field(..., description="Detailed description of the insight")
    suggestion: str = Field(..., description="Suggested improvement")


class EnhancementResponse(BaseModel):
    """Response model for story enhancement."""
    enhanced_story: str = Field(..., description="The enhanced story text")
    insights: List[Insight] = Field(default=[], description="List of insights and suggestions")
    enhancement_id: str = Field(..., description="Unique identifier for this enhancement")
    created_at: str = Field(..., description="ISO timestamp when enhancement was created")