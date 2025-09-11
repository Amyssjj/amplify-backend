"""
Gemini story enhancement service for analyzing photos and enhancing story transcripts.
"""
import os
import json
import re
from typing import Dict, Any
from pydantic import BaseModel, Field
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import base64
import io
from PIL import Image
from app.services.prompt_manager import prompt_manager
from app.services.ai_service_interface import AIStoryEnhancementService
from app.schemas.ai_response import GeminiResponse


class GeminiError(Exception):
    """Custom exception for Gemini service errors."""
    pass


# GeminiResponse is now imported from app.schemas.ai_response


class GeminiService(AIStoryEnhancementService):
    """Service for story enhancement using Google's Gemini AI with vision capabilities."""

    def __init__(self, api_key: str = None, model: str = None):
        """Initialize Gemini service with API configuration."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise GeminiError(
                "GEMINI_API_KEY environment variable is required")

        # Set model with fallback to config default
        self.model_name = model or os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash-lite")

        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

        # Safety settings to allow creative content
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT:
            HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH:
            HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT:
            HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT:
            HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

    async def enhance_story_with_photo(self,
                                       photo_base64: str,
                                       transcript: str,
                                       language: str = "en") -> GeminiResponse:
        """
        Enhance a story transcript using photo analysis with Gemini Vision AI.

        Args:
            photo_base64: Base64 encoded image data
            transcript: Original story transcript
            language: Language code (ISO 639-1)

        Returns:
            GeminiResponse with enhanced transcript and insights

        Raises:
            GeminiError: If validation fails or API call fails
        """
        try:
            # Validate inputs
            self._validate_inputs(photo_base64, transcript, language)

            # Call Gemini API
            response = await self._call_gemini_api(photo_base64=photo_base64,
                                                   transcript=transcript,
                                                   language=language)

            # Validate and return response
            return self._parse_response(response)

        except Exception as e:
            if isinstance(e, GeminiError):
                raise
            raise GeminiError(f"Gemini API error: {str(e)}")

    def _validate_inputs(self, photo_base64: str, transcript: str,
                         language: str) -> None:
        """Validate input parameters."""
        if not photo_base64 or not photo_base64.strip():
            raise GeminiError("Photo data is required")

        if not transcript or not transcript.strip():
            raise GeminiError("Transcript is required")

        if len(transcript) > 5000:
            raise GeminiError("Transcript too long (max 5000 characters)")

        # Validate language code (ISO 639-1)
        valid_languages = {
            'en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'ko', 'zh', 'ru', 'ar',
            'hi'
        }
        if language not in valid_languages:
            raise GeminiError(f"Invalid language code: {language}")

    async def _call_gemini_api(self, photo_base64: str, transcript: str,
                               language: str) -> Dict[str, Any]:
        """Make the actual API call to Gemini."""
        try:
            # Convert base64 to PIL Image
            image_data = base64.b64decode(photo_base64)
            image = Image.open(io.BytesIO(image_data))

            # Convert to RGB mode to ensure compatibility with Gemini API
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparent images
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(
                    image,
                    mask=image.split()[-1] if image.mode in ('RGBA',
                                                             'LA') else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')

            # Build prompt using PromptManager
            prompt = self._build_prompt(transcript, language)

            # Generate content with image and text
            response = self.model.generate_content(
                [prompt, image],
                safety_settings=self.safety_settings,
                generation_config={
                    'temperature': 0.7,
                    'top_p': 0.8,
                    'top_k': 40,
                    'max_output_tokens': 2048,
                })

            # Parse JSON response
            response_text = response.text

            # Extract JSON from response (handle potential markdown formatting)
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```',
                                   response_text, re.DOTALL | re.MULTILINE)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without markdown
                json_str = response_text.strip()

            return json.loads(json_str)

        except json.JSONDecodeError as e:
            raise GeminiError(f"Invalid JSON response from Gemini: {str(e)}")
        except Exception as e:
            raise GeminiError(f"Gemini API call failed: {str(e)}")

    def _build_prompt(self, transcript: str, language: str) -> str:
        """Build the prompt for Gemini story enhancement using PromptManager."""
        # Language mapping for human-readable names
        language_names = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese',
            'ru': 'Russian',
            'ar': 'Arabic',
            'hi': 'Hindi'
        }

        lang_name = language_names.get(language, 'English')

        # Get the social prompt template from PromptManager
        try:
            prompt_template = prompt_manager.get_prompt("social")
            return prompt_template.format(transcript=transcript,
                                          language_name=lang_name)
        except Exception as e:
            # Fallback to error message if prompt loading fails
            raise GeminiError(f"Failed to load prompt template: {str(e)}")

    def _parse_response(self, response: Dict[str, Any]) -> GeminiResponse:
        """Parse and validate Gemini API response."""
        required_fields = ["enhanced_transcript", "insights"]

        for field in required_fields:
            if field not in response:
                raise GeminiError(
                    f"Invalid response format: missing '{field}' field")

        # Validate insights structure
        insights = response.get("insights", {})
        if not isinstance(insights, dict):
            raise GeminiError(
                "Invalid response format: 'insights' must be an object")

        return GeminiResponse(
            enhanced_transcript=response["enhanced_transcript"],
            insights=insights)

    def supports_vision(self) -> bool:
        """Check if this service supports vision/image analysis."""
        return True  # Gemini always supports vision

    def get_provider_name(self) -> str:
        """Get the name of the AI provider."""
        return "gemini"

    async def enhance_youtube_insight(self,
                                     source_transcript: str,
                                     user_transcript: str,
                                     language: str = "en") -> GeminiResponse:
        """
        Enhance a user's YouTube video insight/summary using the source transcript for context.

        Args:
            source_transcript: Original YouTube video transcript
            user_transcript: User's summary or takeaway
            language: Language code (ISO 639-1)

        Returns:
            GeminiResponse with enhanced insight and feedback
        """
        # Validate language code
        valid_languages = {
            'en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'ko', 'zh', 'ru', 'ar', 'hi'
        }
        if language not in valid_languages:
            raise GeminiError(f"Invalid language code: {language}")

        try:
            # Build YouTube-specific prompt
            prompt = self._build_youtube_prompt(source_transcript, user_transcript, language)

            # Generate content without image (text-only)
            response = self.model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config={
                    'temperature': 0.7,
                    'top_p': 0.8,
                    'top_k': 40,
                    'max_output_tokens': 2048,
                }
            )

            # Parse JSON response
            response_text = response.text

            # Extract JSON from response (handle potential markdown formatting)
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```',
                                 response_text, re.DOTALL | re.MULTILINE)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without markdown
                json_str = response_text.strip()

            response_data = json.loads(json_str)
            return self._parse_response(response_data)

        except json.JSONDecodeError as e:
            raise GeminiError(f"Invalid JSON response from Gemini: {str(e)}")
        except Exception as e:
            raise GeminiError(f"YouTube enhancement failed: {str(e)}")

    def _build_youtube_prompt(self, source_transcript: str, user_transcript: str, language: str) -> str:
        """Build the prompt for YouTube insight enhancement using PromptManager."""
        # Language mapping for human-readable names
        language_names = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese',
            'ru': 'Russian',
            'ar': 'Arabic',
            'hi': 'Hindi'
        }
        lang_name = language_names.get(language, 'English')

        # Get the YouTube prompt template from PromptManager
        try:
            prompt_template = prompt_manager.get_prompt("youtube_insight")
            return prompt_template.format(
                source_transcript=source_transcript,
                user_transcript=user_transcript,
                language_name=lang_name
            )
        except Exception as e:
            # Fallback to a basic prompt if template loading fails
            return f"""You are an AI communication coach helping users improve their ability to summarize and extract insights from video content.

Given the following YouTube video transcript and the user's summary/takeaway, provide an enhanced version of their insight along with constructive feedback.

Original Video Transcript:
{source_transcript}

User's Summary/Takeaway:
{user_transcript}

Please respond in {lang_name} with a JSON object containing:
1. "enhanced_transcript": An improved version of the user's summary that is more articulate, insightful, and professionally structured
2. "insights": An object with feedback on:
   - "framework": How well they structured their summary
   - "phrasing": Language and vocabulary usage
   - "synthesis_clarity": How well they captured the key points

Format your response as valid JSON."""
