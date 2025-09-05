"""
Health check endpoints.
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "amplify-backend"}

@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with system information."""
    return {
        "status": "healthy",
        "service": "amplify-backend",
        "version": "1.0.0",
        "uptime": "running"
    }