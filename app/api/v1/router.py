"""
Main API router for version 1 endpoints.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import health, enhancement, audio, auth

# Create the main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(enhancement.router, prefix="/enhance", tags=["enhancement"])
api_router.include_router(audio.router, prefix="/audio", tags=["audio"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])