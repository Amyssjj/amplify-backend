"""
Enhancement endpoints matching OpenAPI specification.
Two-stage flow: POST creates enhancement (text), GET retrieves audio.
"""
import uuid
from fastapi import APIRouter, HTTPException, Query, Path
from app.services.gemini_service import GeminiService, GeminiError
from app.schemas.enhancement import (
    EnhancementRequest, EnhancementTextResponse, 
    EnhancementAudioResponse, EnhancementHistoryResponse,
    EnhancementDetails
)

router = APIRouter()

@router.post("", response_model=EnhancementTextResponse)
async def create_enhancement(request: EnhancementRequest):
    """Create enhancement (Stage 1 - Text).
    
    Performs Gemini analysis on a photo and transcript.
    Responds quickly with text-based results. The client app should immediately
    call GET /api/v1/enhancements/{id}/audio in the background to complete the flow.
    """
    try:
        # Generate unique enhancement ID
        enhancement_id = f"enh_{uuid.uuid4().hex[:12]}"
        
        # Initialize Gemini service
        gemini_service = GeminiService()
        
        # Enhance story with photo analysis
        enhancement_result = await gemini_service.enhance_story_with_photo(
            photo_base64=request.photo_base64,
            transcript=request.transcript,
            language=request.language
        )
        
        # TODO: Save to database (will implement in next step)
        
        return EnhancementTextResponse(
            enhancement_id=enhancement_id,
            enhanced_transcript=enhancement_result.enhanced_transcript,
            insights=enhancement_result.insights
        )
    except GeminiError as e:
        # Handle specific Gemini service errors
        if "API key" in str(e):
            raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
        elif "rate limit" in str(e).lower():
            raise HTTPException(status_code=429, detail="Too many requests, please try again later")
        else:
            raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=EnhancementHistoryResponse)
async def get_enhancements(
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0)
):
    """Get enhancement history.
    
    Returns a paginated list of the user's past enhancements, including audio status.
    """
    try:
        # TODO: Implement database query with pagination
        return EnhancementHistoryResponse(
            total=0,
            items=[]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{enhancement_id}", response_model=EnhancementDetails)
async def get_enhancement_by_id(
    enhancement_id: str = Path(..., pattern=r"^enh_[a-zA-Z0-9]+$")
):
    """Get enhancement details.
    
    Returns the full persisted details of a specific enhancement, including its audio status.
    """
    try:
        # TODO: Implement database query by ID
        return EnhancementDetails(
            enhancement_id=enhancement_id,
            created_at="2025-09-07T00:00:00Z",
            original_transcript="Original story...",
            enhanced_transcript="Enhanced story...",
            insights={"plot": "Good story structure"},
            audio_status="not_generated",
            photo_base64=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{enhancement_id}/audio", response_model=EnhancementAudioResponse)
async def get_enhancement_audio(
    enhancement_id: str = Path(..., pattern=r"^enh_[a-zA-Z0-9]+$")
):
    """Generate or retrieve audio (Stage 2 - Audio).
    
    Generates TTS audio for the given enhancement. This is a synchronous, idempotent endpoint.
    The client app should call this in the background immediately after Stage 1 succeeds.
    The response contains the Base64 audio data for the client to save locally.
    """
    try:
        # TODO: Implement TTS generation logic
        return EnhancementAudioResponse(
            audio_base64="UklGRnoGAABXQVZFZm10IBAAAAABAAEA...",  # Placeholder
            audio_format="mp3"
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Enhancement not found")
        elif "tts" in str(e).lower():
            raise HTTPException(status_code=503, detail="TTS service unavailable")
        else:
            raise HTTPException(status_code=500, detail=str(e))