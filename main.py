"""
Amplify Backend - Main Application Entry Point
"""
import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

# Database initialization using lifespan
@asynccontextmanager
async def lifespan(app_instance):
    """Initialize database on application startup."""
    try:
        from app.core.database import create_tables
        create_tables()
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
        # Don't fail startup if database is not available
        pass
    yield
    # Cleanup (if needed)

# Create FastAPI app instance
app = FastAPI(
    title="Amplify Backend API",
    description="Backend service for the Amplify application",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Amplify Backend API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "amplify-backend"}

if __name__ == "__main__":
    # Use port 8000 for local development (matches OpenAPI spec)
    # Replit will override this with port 5000 via .replit configuration
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )