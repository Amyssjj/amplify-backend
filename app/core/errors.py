"""
Centralized error handling utilities using utility schemas.
"""
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import List

from app.schemas.utility import ErrorResponse, ValidationErrorResponse, ValidationError


def create_error_response(status_code: int, error_code: str, message: str) -> JSONResponse:
    """Create a standardized error response using ErrorResponse schema."""
    error_response = ErrorResponse(error=error_code, message=message)
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump()
    )


def create_validation_error_response(errors: List[dict]) -> JSONResponse:
    """Create a standardized validation error response."""
    validation_errors = []
    for error in errors:
        loc = error.get("loc", [])
        field = ".".join(str(x) for x in loc[1:]) if len(loc) > 1 else "unknown"
        validation_errors.append(
            ValidationError(
                field=field,
                message=error.get("msg", "Validation error")
            )
        )

    error_response = ValidationErrorResponse(
        error="VALIDATION_ERROR",
        message="Request validation failed",
        validation_errors=validation_errors
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump()
    )


def not_found_error(resource: str = "Resource") -> HTTPException:
    """Create a standardized 404 error."""
    error_response = ErrorResponse(
        error="NOT_FOUND",
        message=f"{resource} not found"
    )
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=error_response.model_dump()
    )


def unauthorized_error(message: str = "Unauthorized", headers: dict = None) -> HTTPException:
    """Create a standardized 401 error."""
    error_response = ErrorResponse(
        error="UNAUTHORIZED",
        message=message
    )
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=error_response.model_dump(),
        headers=headers
    )


def service_unavailable_error(service: str = "Service") -> HTTPException:
    """Create a standardized 503 error."""
    error_response = ErrorResponse(
        error="SERVICE_UNAVAILABLE",
        message=f"{service} temporarily unavailable"
    )
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=error_response.model_dump()
    )


def internal_server_error(message: str = "Internal server error") -> HTTPException:
    """Create a standardized 500 error."""
    error_response = ErrorResponse(
        error="INTERNAL_ERROR",
        message=message
    )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=error_response.model_dump()
    )
