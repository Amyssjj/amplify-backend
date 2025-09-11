"""
Main API router for version 1 endpoints.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import health, enhancement, auth, tts
from app.api.v1 import youtube_cards

# Create the main API router
api_router = APIRouter()

# Include all endpoint routers matching OpenAPI specification
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(enhancement.router, prefix="/enhancements", tags=["Enhancement"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(tts.router, prefix="/tts", tags=["TTS"])
api_router.include_router(youtube_cards.router, tags=["YouTube"])
