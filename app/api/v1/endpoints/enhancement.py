"""
Enhancement endpoints matching OpenAPI specification.
Two-stage flow: POST creates enhancement (text), GET retrieves audio.
"""
import uuid
from typing import Union
from fastapi import APIRouter, HTTPException, Query, Path, Depends, Body
from sqlalchemy.orm import Session

from app.services.gemini_service import GeminiService, GeminiError
from app.services.tts_service import TTSService, TTSError
from app.core.database import get_db_session
from app.core.auth import get_user_id_or_anonymous
from app.models.enhancement import Enhancement, PromptTypeEnum
from app.schemas.enhancement import (
    LegacyEnhancementRequest,
    EnhancementTextResponse,
    EnhancementAudioResponse,
    EnhancementHistoryResponse,
    EnhancementDetails,
    EnhancementSummary,
    PromptType
)
from app.schemas.youtube import PhotoEnhancementRequest, YouTubeEnhancementRequest

router = APIRouter()


@router.post("", response_model=EnhancementTextResponse)
async def create_enhancement(
    request: Union[PhotoEnhancementRequest, YouTubeEnhancementRequest, LegacyEnhancementRequest] = Body(...),
    db: Session = Depends(get_db_session),
    user_id: str = Depends(get_user_id_or_anonymous)
):
    """Create enhancement (Stage 1 - Text).

    Performs Gemini analysis on a user transcript based on a specific prompt
    context (either a photo or a YouTube insight). Responds quickly with
    text-based results. The client app should immediately call
    GET /api/v1/enhancements/{id}/audio in the background to complete the flow.
    """
    try:
        # Generate unique enhancement ID
        enhancement_id = f"enh_{uuid.uuid4().hex[:12]}"

        # Initialize Gemini service
        gemini_service = GeminiService()

        # Handle different request types
        if isinstance(request, PhotoEnhancementRequest):
            # Photo enhancement flow
            enhancement_result = await gemini_service.enhance_story_with_photo(
                photo_base64=request.photo_base64,
                transcript=request.transcript,
                language=request.language
            )

            prompt_type = PromptTypeEnum.PHOTO
            prompt_title = "Photo Story"
            source_photo_base64 = request.photo_base64
            source_transcript = None

        elif isinstance(request, YouTubeEnhancementRequest):
            # YouTube enhancement flow
            enhancement_result = await gemini_service.enhance_youtube_insight(
                source_transcript=request.source_transcript,
                user_transcript=request.transcript,
                language=request.language
            )

            prompt_type = PromptTypeEnum.YOUTUBE
            prompt_title = "YouTube Insight"
            source_photo_base64 = None
            source_transcript = request.source_transcript

        else:
            # Legacy photo enhancement (backward compatibility)
            enhancement_result = await gemini_service.enhance_story_with_photo(
                photo_base64=request.photo_base64,
                transcript=request.transcript,
                language=request.language
            )

            prompt_type = PromptTypeEnum.PHOTO
            prompt_title = "Photo Story"
            source_photo_base64 = request.photo_base64
            source_transcript = None

        # Save to database
        try:
            enhancement = Enhancement(
                enhancement_id=enhancement_id,
                user_id=user_id,
                prompt_type=prompt_type,
                prompt_title=prompt_title,
                source_photo_base64=source_photo_base64,
                source_transcript=source_transcript,
                user_transcript=request.transcript,
                enhanced_transcript=enhancement_result.enhanced_transcript,
                insights=enhancement_result.insights,
                language=request.language
            )

            db.add(enhancement)
            db.commit()
            db.refresh(enhancement)
            print(f"✅ Enhancement saved to database: {enhancement_id}")

        except Exception as db_error:
            db.rollback()
            print(f"⚠️ Database save failed: {db_error}")
            # Continue without database persistence for now

        return EnhancementTextResponse(
            enhancement_id=enhancement_id,
            enhanced_transcript=enhancement_result.enhanced_transcript,
            insights=enhancement_result.insights
        )

    except GeminiError as e:
        # Handle specific Gemini service errors
        print(f"❌ GeminiError: {e}")
        if "API key" in str(e):
            raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
        elif "rate limit" in str(e).lower():
            raise HTTPException(status_code=429, detail="Too many requests, please try again later")
        else:
            raise HTTPException(status_code=503, detail="AI service temporarily unavailable")

    except Exception as e:
        print(f"❌ Enhancement error: {e}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
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
        # Query enhancements for user
        query = db.query(Enhancement).filter(Enhancement.user_id == user_id)

        # Get total count
        total = query.count()

        # Apply pagination
        enhancements = query.order_by(Enhancement.created_at.desc()).offset(offset).limit(limit).all()

        # Convert to response models
        items = []
        for e in enhancements:
            # Create appropriate thumbnail based on prompt type
            prompt_youtube_thumbnail_url = None
            prompt_photo_thumbnail_base64 = None

            if e.prompt_type == PromptTypeEnum.PHOTO and e.source_photo_base64:
                # For photo enhancements, create a small thumbnail (first 100 chars of base64)
                prompt_photo_thumbnail_base64 = e.source_photo_base64[:100] if len(e.source_photo_base64) > 100 else e.source_photo_base64

            items.append(EnhancementSummary(
                enhancement_id=e.enhancement_id,
                created_at=e.created_at,
                prompt_type=PromptType(e.prompt_type.value),
                prompt_title=e.prompt_title or "Untitled",
                prompt_youtube_thumbnail_url=prompt_youtube_thumbnail_url,
                prompt_photo_thumbnail_base64=prompt_photo_thumbnail_base64,
                transcript_preview=e.enhanced_transcript[:100] if e.enhanced_transcript else "",
                audio_status=e.audio_status.value,
                audio_duration_seconds=e.audio_duration_seconds
            ))

        return EnhancementHistoryResponse(total=total, items=items)

    except Exception as e:
        print(f"❌ Error fetching enhancements: {e}")
        # Return empty list on error
        return EnhancementHistoryResponse(total=0, items=[])


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
        # Query specific enhancement
        enhancement = db.query(Enhancement).filter(
            Enhancement.enhancement_id == enhancement_id,
            Enhancement.user_id == user_id
        ).first()

        if not enhancement:
            raise HTTPException(status_code=404, detail="Enhancement not found")

        return EnhancementDetails(
            enhancement_id=enhancement.enhancement_id,
            created_at=enhancement.created_at,
            prompt_type=PromptType(enhancement.prompt_type.value),
            prompt_title=enhancement.prompt_title,
            prompt_youtube_thumbnail_url=None,  # Would be populated if we had YouTube card reference
            source_photo_base64=enhancement.source_photo_base64,
            source_transcript=enhancement.source_transcript,
            user_transcript=enhancement.user_transcript,
            enhanced_transcript=enhancement.enhanced_transcript,
            insights=enhancement.insights,
            audio_status=enhancement.audio_status.value,
            audio_duration_seconds=enhancement.audio_duration_seconds
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching enhancement {enhancement_id}: {e}")
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
        # Retrieve enhancement
        enhancement = db.query(Enhancement).filter(
            Enhancement.enhancement_id == enhancement_id,
            Enhancement.user_id == user_id
        ).first()

        if not enhancement:
            raise HTTPException(status_code=404, detail="Enhancement not found")

        # Initialize TTS service
        tts_service = TTSService()

        # Generate audio
        audio_base64 = await tts_service.generate_speech(
            text=enhancement.enhanced_transcript,
            language=enhancement.language
        )

        # Update audio status in database
        try:
            enhancement.audio_status = "ready"
            db.commit()
            print(f"✅ Audio status updated for: {enhancement_id}")
        except Exception as db_error:
            print(f"⚠️ Failed to update audio status: {db_error}")
            # Continue even if status update fails

        return EnhancementAudioResponse(
            audio_base64=audio_base64,
            audio_format="mp3"
        )

    except HTTPException:
        raise
    except TTSError as e:
        print(f"❌ TTS error: {e}")
        raise HTTPException(status_code=503, detail="TTS service unavailable")
    except Exception as e:
        print(f"❌ Audio generation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
