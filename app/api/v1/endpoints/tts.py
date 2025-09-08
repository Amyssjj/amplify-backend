"""
TTS (Text-to-Speech) configuration and testing endpoints.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from app.services.tts_service import TTSService, TTSError

router = APIRouter()


class TTSStatusResponse(BaseModel):
    """TTS service status response."""
    current_provider: str = Field(..., description="Currently configured TTS provider")
    current_voice: str = Field(..., description="Currently configured voice")
    providers: Dict[str, Dict] = Field(..., description="Available TTS providers and their status")
    supported_languages: List[str] = Field(..., description="Supported language codes")


class VoicesResponse(BaseModel):
    """Available voices response."""
    providers: Dict[str, List[Dict]] = Field(..., description="Available voices by provider")


@router.get("/status", response_model=TTSStatusResponse)
async def get_tts_status():
    """Get TTS service status and available providers."""
    try:
        tts_service = TTSService()
        
        # Test all providers
        provider_status = await tts_service.test_service()
        
        # Get current configuration
        from app.core.config import settings
        
        return TTSStatusResponse(
            current_provider=settings.tts_provider,
            current_voice=settings.tts_voice,
            providers=provider_status,
            supported_languages=tts_service.get_supported_languages()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get TTS status: {str(e)}")


@router.get("/voices", response_model=VoicesResponse)
async def get_available_voices():
    """Get available voices for all TTS providers."""
    try:
        tts_service = TTSService()
        voices = tts_service.get_available_voices()
        
        return VoicesResponse(providers=voices)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get voices: {str(e)}")


@router.post("/test")
async def test_tts_generation(
    text: str = "Hello, this is a test of the text-to-speech service.",
    language: str = "en",
    provider: Optional[str] = None
):
    """Test TTS generation with specified text and provider."""
    try:
        tts_service = TTSService()
        
        # Temporarily override provider if specified
        if provider:
            original_provider = tts_service.settings.tts_provider if hasattr(tts_service, 'settings') else None
            from app.core.config import settings
            settings.tts_provider = provider
        
        # Generate test audio
        audio_base64, audio_format = await tts_service.generate_audio(
            text=text,
            language=language
        )
        
        # Restore original provider
        if provider and original_provider:
            settings.tts_provider = original_provider
        
        return {
            "success": True,
            "provider_used": provider or "default",
            "audio_format": audio_format,
            "audio_size_bytes": len(audio_base64),
            "message": "TTS generation successful"
        }
        
    except TTSError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"TTS generation failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS test failed: {str(e)}")