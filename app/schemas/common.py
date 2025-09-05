"""
Common schemas used across the application.
"""
from pydantic import BaseModel, Field
from typing import Optional


class ErrorResponse(BaseModel):
    """Standard error response model."""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(default=None, description="Machine-readable error code")


class SuccessResponse(BaseModel):
    """Standard success response model."""
    message: str = Field(..., description="Success message")
    data: Optional[dict] = Field(default=None, description="Optional response data")