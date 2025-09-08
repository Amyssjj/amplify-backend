"""
Text-to-Speech service supporting OpenAI TTS and ElevenLabs TTS.
Converts enhanced transcripts to audio for the mobile app.
"""
import base64
import io
from typing import Optional, Tuple
from app.core.config import settings
import logging

# Try to import TTS libraries, fall back to mock implementation if unavailable
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

logger = logging.getLogger(__name__)


class TTSError(Exception):
    """Custom exception for TTS service errors."""
    pass


class TTSService:
    """Text-to-Speech service supporting multiple providers."""
    
    def __init__(self):
        self.openai_client = None
        self.elevenlabs_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize TTS clients based on available API keys."""
        # Initialize OpenAI client
        if OPENAI_AVAILABLE and settings.openai_api_key:
            try:
                self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
                logger.info("✅ OpenAI TTS client initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize OpenAI TTS client: {e}")
                self.openai_client = None
        elif not OPENAI_AVAILABLE:
            logger.warning("⚠️ OpenAI library not available")
            
        # Initialize ElevenLabs
        if ELEVENLABS_AVAILABLE and settings.elevenlabs_api_key:
            try:
                self.elevenlabs_client = ElevenLabs(api_key=settings.elevenlabs_api_key)
                logger.info("✅ ElevenLabs TTS initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize ElevenLabs TTS: {e}")
                self.elevenlabs_client = None
        elif not ELEVENLABS_AVAILABLE:
            logger.warning("⚠️ ElevenLabs library not available")
    
    async def generate_audio(
        self, 
        text: str, 
        language: str = "en",
        voice: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate audio from text using configured TTS provider.
        
        Args:
            text: The enhanced transcript to convert to speech
            language: Language code (e.g., 'en', 'es', 'fr')
            voice: Voice name (provider-specific)
            
        Returns:
            Tuple of (base64_audio_data, audio_format)
            
        Raises:
            TTSError: If TTS generation fails
        """
        if not text or not text.strip():
            raise TTSError("Text content is required")
        
        # Limit text length to prevent abuse and long processing times
        max_length = 4096  # OpenAI limit
        if len(text) > max_length:
            logger.warning(f"Text truncated from {len(text)} to {max_length} characters")
            text = text[:max_length] + "..."
        
        # Determine which provider to use
        provider = settings.tts_provider.lower()
        
        if provider == "openai" and self.openai_client:
            return await self._generate_openai_audio(text, language, voice)
        elif provider == "elevenlabs" and self.elevenlabs_client:
            return await self._generate_elevenlabs_audio(text, language, voice)
        else:
            # Fall back to mock implementation
            logger.info(f"🔧 Using mock TTS (provider: {provider}, openai: {bool(self.openai_client)}, elevenlabs: {bool(self.elevenlabs_client)})")
            return await self._generate_mock_audio(text, language)
    
    async def _generate_openai_audio(
        self, 
        text: str, 
        language: str, 
        voice: Optional[str] = None
    ) -> Tuple[str, str]:
        """Generate audio using OpenAI TTS."""
        try:
            # Use configured voice or default
            voice_name = voice or settings.tts_voice or "alloy"
            
            # Validate voice name
            valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            if voice_name not in valid_voices:
                logger.warning(f"Invalid OpenAI voice '{voice_name}', using 'alloy'")
                voice_name = "alloy"
            
            logger.info(f"🔊 Generating OpenAI TTS audio: {len(text)} chars, voice: {voice_name}")
            
            response = self.openai_client.audio.speech.create(
                model="tts-1",  # or "tts-1-hd" for higher quality
                voice=voice_name,
                input=text,
                response_format="mp3"
            )
            
            # Convert response to base64
            audio_data = response.content
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            logger.info(f"✅ OpenAI audio generated successfully ({len(audio_base64)} base64 chars)")
            return audio_base64, "mp3"
            
        except Exception as e:
            logger.error(f"❌ OpenAI TTS generation failed: {e}")
            if "rate limit" in str(e).lower():
                raise TTSError("OpenAI TTS rate limit exceeded, please try again later")
            elif "quota" in str(e).lower():
                raise TTSError("OpenAI TTS quota exceeded")
            elif "api key" in str(e).lower():
                raise TTSError("OpenAI TTS authentication failed")
            else:
                raise TTSError(f"OpenAI TTS generation failed: {str(e)}")
    
    async def _generate_elevenlabs_audio(
        self, 
        text: str, 
        language: str, 
        voice: Optional[str] = None
    ) -> Tuple[str, str]:
        """Generate audio using ElevenLabs TTS."""
        try:
            # Use provided voice or get default voice for language
            voice_name = voice or self._get_elevenlabs_voice(language)
            
            logger.info(f"🔊 Generating ElevenLabs TTS audio: {len(text)} chars, voice: {voice_name}")
            
            # Generate audio using the ElevenLabs client
            response = self.elevenlabs_client.text_to_speech.convert(
                text=text,
                voice_id=voice_name,
                model_id="eleven_monolingual_v1"
            )
            
            # Collect audio bytes
            audio_data = b""
            for chunk in response:
                audio_data += chunk
            
            # Convert to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            logger.info(f"✅ ElevenLabs audio generated successfully ({len(audio_base64)} base64 chars)")
            return audio_base64, "mp3"
            
        except Exception as e:
            logger.error(f"❌ ElevenLabs TTS generation failed: {e}")
            if "rate limit" in str(e).lower():
                raise TTSError("ElevenLabs TTS rate limit exceeded, please try again later")
            elif "quota" in str(e).lower():
                raise TTSError("ElevenLabs TTS quota exceeded")
            elif "api key" in str(e).lower() or "unauthorized" in str(e).lower():
                raise TTSError("ElevenLabs TTS authentication failed")
            else:
                raise TTSError(f"ElevenLabs TTS generation failed: {str(e)}")
    
    def _get_elevenlabs_voice(self, language: str) -> str:
        """Get appropriate ElevenLabs voice for language."""
        # Map language codes to ElevenLabs voice IDs (these are common pre-made voices)
        voice_map = {
            "en": "21m00Tcm4TlvDq8ikWAM",  # Rachel - Clear female American voice
            "es": "VR6AewLTigWG4xSOukaG",  # Sofia - Spanish voice  
            "fr": "XB0fDUnXU5powFXDhCwa",  # Charlotte - French voice
            "de": "jBpfuIE2acCO8z3wKNLl",  # Gigi - German voice
            "it": "oWAxZDx7w5VEj9dCyTzz",  # Giulia - Italian voice
            "pt": "pMsXgVXv3BLzUgSXRplE",  # Liam - Portuguese voice
        }
        
        return voice_map.get(language.lower(), "21m00Tcm4TlvDq8ikWAM")  # Default to Rachel
    
    async def _generate_mock_audio(self, text: str, language: str) -> Tuple[str, str]:
        """
        Generate mock audio for development/testing when TTS providers are unavailable.
        Returns a small MP3 file encoded as base64.
        """
        logger.info(f"🔧 Using mock TTS for {len(text)} characters in {language}")
        
        # Create a minimal MP3 header for a valid but silent audio file
        # This is a minimal MP3 frame that represents silence
        mock_mp3_data = bytes([
            0xFF, 0xFB, 0x90, 0x00,  # MP3 header
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Padding
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        ])
        
        # Encode to base64
        audio_base64 = base64.b64encode(mock_mp3_data).decode('utf-8')
        
        logger.info("✅ Mock audio generated successfully")
        return audio_base64, "mp3"
    
    def get_supported_languages(self) -> list:
        """Get list of supported language codes."""
        return ["en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh", "ar", "hi", "nl", "pl", "ru"]
    
    def get_available_voices(self, provider: Optional[str] = None) -> dict:
        """Get available voices for each provider."""
        voices_dict = {}
        
        # OpenAI voices
        if self.openai_client or provider == "openai":
            voices_dict["openai"] = [
                {"name": "alloy", "description": "Balanced, neutral voice"},
                {"name": "echo", "description": "Deep, authoritative voice"},
                {"name": "fable", "description": "Expressive, storytelling voice"},
                {"name": "onyx", "description": "Deep, professional voice"},
                {"name": "nova", "description": "Bright, energetic voice"},
                {"name": "shimmer", "description": "Soft, gentle voice"}
            ]
        
        # ElevenLabs voices (commonly available)
        if self.elevenlabs_client or provider == "elevenlabs":
            voices_dict["elevenlabs"] = [
                {"name": "Rachel", "description": "Clear female American voice"},
                {"name": "Domi", "description": "Strong female American voice"},
                {"name": "Bella", "description": "Soft female American voice"},
                {"name": "Antoni", "description": "Well-rounded male American voice"},
                {"name": "Elli", "description": "Emotional female American voice"},
                {"name": "Josh", "description": "Deep male American voice"},
                {"name": "Arnold", "description": "Crisp male American voice"},
                {"name": "Adam", "description": "Deep male American voice"},
                {"name": "Sam", "description": "Raspy male American voice"}
            ]
        
        return voices_dict
    
    async def test_service(self) -> dict:
        """Test TTS service providers and return status."""
        results = {
            "openai": {"available": False, "working": False},
            "elevenlabs": {"available": False, "working": False}
        }
        
        # Test OpenAI
        if self.openai_client:
            results["openai"]["available"] = True
            try:
                await self._generate_openai_audio("Hello, this is a test.", "en")
                results["openai"]["working"] = True
            except Exception as e:
                logger.error(f"OpenAI TTS test failed: {e}")
        
        # Test ElevenLabs
        if self.elevenlabs_client:
            results["elevenlabs"]["available"] = True
            try:
                await self._generate_elevenlabs_audio("Hello, this is a test.", "en")
                results["elevenlabs"]["working"] = True
            except Exception as e:
                logger.error(f"ElevenLabs TTS test failed: {e}")
        
        return results