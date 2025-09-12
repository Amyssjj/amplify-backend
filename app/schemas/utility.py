"""
Utility schemas for health checks and error responses matching OpenAPI specification.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class ServiceStatus(str, Enum):
    """Service readiness status."""
    READY = "ready"
    NOT_READY = "not_ready"


class HealthStatus(str, Enum):
    """Basic health status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class ServiceStatusDict(BaseModel):
    """Status of individual services."""
    gemini: bool = Field(..., description="Gemini service availability")
    tts: bool = Field(..., description="TTS service availability")
    database: bool = Field(..., description="Database connection status")


class ReadinessResponse(BaseModel):
    """Detailed health check response (OpenAPI ReadinessResponse)."""
    status: ServiceStatus = Field(..., description="Overall service readiness status")
    services: ServiceStatusDict = Field(..., description="Individual service statuses")


class BasicHealthResponse(BaseModel):
    """Basic health check response."""
    status: str = Field(..., description="Service health status", example="healthy")
    service: str = Field(..., description="Service name", example="amplify-backend")


class ErrorResponse(BaseModel):
    """Standard error response (OpenAPI ErrorResponse)."""
    error: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")


class ValidationError(BaseModel):
    """Individual validation error."""
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")


class ValidationErrorResponse(BaseModel):
    """Validation error response for 400 errors (OpenAPI ValidationErrorResponse)."""
    error: str = Field(default="VALIDATION_ERROR", description="Error type")
    message: str = Field(..., description="General error message")
    validation_errors: List[ValidationError] = Field(..., description="List of validation errors")
