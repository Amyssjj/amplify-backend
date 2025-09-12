"""
Amplify Backend - Main Application Entry Point
"""
import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import create_validation_error_response, create_error_response

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

# Add global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with standardized response."""
    return create_validation_error_response(exc.errors())

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with standardized response."""
    return create_error_response(
        status_code=500,
        error_code="INTERNAL_ERROR",
        message="An unexpected error occurred"
    )

@app.get("/")
async def root():
    """Root endpoint - Welcome message"""
    return {
        "message": "Amplify Backend API",
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health/"
    }

if __name__ == "__main__":
    # Use port 5000 for Replit deployment (required for proper deployment)
    # Replit will override this with PORT environment variable
    port = int(os.getenv("PORT", 5000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
