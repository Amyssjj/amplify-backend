"""
Health check endpoints.
"""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.schemas.utility import BasicHealthResponse, ReadinessResponse, ServiceStatus, ServiceStatusDict
from app.core.config import settings

router = APIRouter()

@router.get("/", response_model=BasicHealthResponse)
async def health_check():
    """Basic health check endpoint."""
    return BasicHealthResponse(
        status="healthy",
        service="amplify-backend"
    )

@router.get("/detailed", response_model=ReadinessResponse)
async def detailed_health_check():
    """Detailed health check with system information."""
    # Check database connectivity
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        database_ok = True
    except Exception:
        database_ok = False

    # Check Gemini service
    try:
        gemini_ok = bool(settings.GEMINI_API_KEY)
    except Exception:
        gemini_ok = False

    # Check TTS service
    try:
        tts_ok = settings.TTS_PROVIDER in ["openai", "elevenlabs", "mock"]
        if settings.TTS_PROVIDER == "openai":
            tts_ok = tts_ok and bool(settings.OPENAI_API_KEY)
        elif settings.TTS_PROVIDER == "elevenlabs":
            tts_ok = tts_ok and bool(settings.ELEVENLABS_API_KEY)
    except Exception:
        tts_ok = False

    # Determine overall status
    all_ok = database_ok and gemini_ok and tts_ok
    overall_status = ServiceStatus.READY if all_ok else ServiceStatus.NOT_READY

    response = ReadinessResponse(
        status=overall_status,
        services=ServiceStatusDict(
            gemini=gemini_ok,
            tts=tts_ok,
            database=database_ok
        )
    )

    # Return 503 if not ready
    if overall_status == ServiceStatus.NOT_READY:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response.model_dump()
        )

    return response
