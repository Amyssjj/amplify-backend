"""
Enhancement endpoints matching OpenAPI specification.
Two-stage flow: POST creates enhancement (text), GET retrieves audio.
"""
import uuid
from fastapi import APIRouter, HTTPException, Query, Path, Depends
from sqlalchemy.orm import Session
from app.services.gemini_service import GeminiService, GeminiError
from app.services.tts_service import TTSService, TTSError
from app.core.database import get_db_session
from app.core.auth import get_user_id_or_anonymous
from app.models.enhancement import Enhancement
from app.schemas.enhancement import (
    EnhancementRequest, EnhancementTextResponse, 
    EnhancementAudioResponse, EnhancementHistoryResponse,
    EnhancementDetails
)

router = APIRouter()

@router.post("", response_model=EnhancementTextResponse)
async def create_enhancement(
    request: EnhancementRequest
):
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
        
        # TODO: Save to database - temporarily disabled to isolate AI service issue
        print(f"✅ Enhancement created: {enhancement_id}")
        print(f"📝 Enhanced transcript: {enhancement_result.enhanced_transcript[:100]}...")
        
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
        print(f"❌ Enhancement error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=EnhancementHistoryResponse)
async def get_enhancements(
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
    user_id: str = Depends(get_user_id_or_anonymous)
):
    """Get enhancement history.
    
    Returns a paginated list of the user's past enhancements, including audio status.
    """
    try:
        # Query enhancements with pagination (filtered by user)
        total_count = db.query(Enhancement).filter(Enhancement.user_id == user_id).count()
        
        enhancements = db.query(Enhancement)\
            .filter(Enhancement.user_id == user_id)\
            .order_by(Enhancement.created_at.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()
        
        # Convert to response format
        items = []
        for enhancement in enhancements:
            # Create transcript preview (first 100 characters)
            preview = enhancement.enhanced_transcript[:100]
            if len(enhancement.enhanced_transcript) > 100:
                preview += "..."
            
            items.append({
                "enhancement_id": enhancement.enhancement_id,
                "created_at": enhancement.created_at,
                "transcript_preview": preview,
                "audio_status": enhancement.audio_status.value
            })
        
        return EnhancementHistoryResponse(
            total=total_count,
            items=items
        )
        
    except Exception as e:
        # If database fails, return empty list
        print(f"⚠️ Database query failed: {e}")
        return EnhancementHistoryResponse(
            total=0,
            items=[]
        )

@router.get("/{enhancement_id}", response_model=EnhancementDetails)
async def get_enhancement_by_id(
    enhancement_id: str = Path(..., pattern=r"^enh_[a-zA-Z0-9]+$"),
    db: Session = Depends(get_db_session),
    user_id: str = Depends(get_user_id_or_anonymous)
):
    """Get enhancement details.
    
    Returns the full persisted details of a specific enhancement, including its audio status.
    """
    try:
        # Query enhancement by ID and user
        enhancement = db.query(Enhancement).filter(
            Enhancement.enhancement_id == enhancement_id,
            Enhancement.user_id == user_id
        ).first()
        
        if not enhancement:
            raise HTTPException(status_code=404, detail="Enhancement not found")
        
        return EnhancementDetails(
            enhancement_id=enhancement.enhancement_id,
            created_at=enhancement.created_at,
            original_transcript=enhancement.original_transcript,
            enhanced_transcript=enhancement.enhanced_transcript,
            insights=enhancement.insights,
            audio_status=enhancement.audio_status.value,
            photo_base64=enhancement.photo_base64
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"⚠️ Database query failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{enhancement_id}/audio", response_model=EnhancementAudioResponse)
async def get_enhancement_audio(
    enhancement_id: str = Path(..., pattern=r"^enh_[a-zA-Z0-9]+$"),
    db: Session = Depends(get_db_session),
    user_id: str = Depends(get_user_id_or_anonymous)
):
    """Generate or retrieve audio (Stage 2 - Audio).
    
    Generates TTS audio for the given enhancement. This is a synchronous, idempotent endpoint.
    The client app should call this in the background immediately after Stage 1 succeeds.
    The response contains the Base64 audio data for the client to save locally.
    """
    try:
        # Get enhancement from database
        enhancement = db.query(Enhancement).filter(
            Enhancement.enhancement_id == enhancement_id,
            Enhancement.user_id == user_id
        ).first()
        
        if not enhancement:
            raise HTTPException(status_code=404, detail="Enhancement not found")
        
        # Initialize TTS service
        tts_service = TTSService()
        
        # Generate audio from enhanced transcript
        audio_base64, audio_format = await tts_service.generate_audio(
            text=enhancement.enhanced_transcript,
            language=enhancement.language
        )
        
        # Update enhancement audio status in database
        try:
            from app.models.enhancement import AudioStatusEnum
            enhancement.audio_status = AudioStatusEnum.READY
            db.commit()
        except Exception as db_error:
            # Log but don't fail the request if database update fails
            print(f"⚠️ Failed to update audio status: {db_error}")
            db.rollback()
        
        return EnhancementAudioResponse(
            audio_base64=audio_base64,
            audio_format=audio_format
        )
        
    except TTSError as e:
        # Handle specific TTS service errors
        if "quota" in str(e).lower() or "limit" in str(e).lower():
            raise HTTPException(status_code=429, detail="TTS service quota exceeded, please try again later")
        elif "credentials" in str(e).lower() or "authentication" in str(e).lower():
            raise HTTPException(status_code=503, detail="TTS service temporarily unavailable")
        else:
            raise HTTPException(status_code=503, detail="TTS service unavailable")
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        print(f"❌ Audio generation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")