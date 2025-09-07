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


class GeminiError(Exception):
    """Custom exception for Gemini service errors."""
    pass


class GeminiResponse(BaseModel):
    """Response model for Gemini story enhancement."""
    enhanced_transcript: str = Field(..., description="Enhanced version of the original story")
    insights: Dict[str, str] = Field(..., description="Analysis insights about the enhancements made")


class GeminiService:
    """Service for story enhancement using Google's Gemini AI with vision capabilities."""
    
    def __init__(self, api_key: str = None):
        """Initialize Gemini service with API configuration."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise GeminiError("GEMINI_API_KEY environment variable is required")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro-vision')
        
        # Safety settings to allow creative content
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
    
    async def enhance_story_with_photo(self, photo_base64: str, transcript: str, language: str = "en") -> GeminiResponse:
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
            response = await self._call_gemini_api(
                photo_base64=photo_base64,
                transcript=transcript,
                language=language
            )
            
            # Validate and return response
            return self._parse_response(response)
            
        except Exception as e:
            if isinstance(e, GeminiError):
                raise
            raise GeminiError(f"Gemini API error: {str(e)}")
    
    def _validate_inputs(self, photo_base64: str, transcript: str, language: str) -> None:
        """Validate input parameters."""
        if not photo_base64 or not photo_base64.strip():
            raise GeminiError("Photo data is required")
        
        if not transcript or not transcript.strip():
            raise GeminiError("Transcript is required")
        
        if len(transcript) > 5000:
            raise GeminiError("Transcript too long (max 5000 characters)")
        
        # Validate language code (ISO 639-1)
        valid_languages = {
            'en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'ko', 'zh', 'ru', 'ar', 'hi'
        }
        if language not in valid_languages:
            raise GeminiError(f"Invalid language code: {language}")
    
    async def _call_gemini_api(self, photo_base64: str, transcript: str, language: str) -> Dict[str, Any]:
        """Make the actual API call to Gemini."""
        try:
            # Convert base64 to PIL Image
            image_data = base64.b64decode(photo_base64)
            image = Image.open(io.BytesIO(image_data))
            
            # Build prompt
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
                }
            )
            
            # Parse JSON response
            response_text = response.text
            
            # Extract JSON from response (handle potential markdown formatting)
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
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
        """Build the prompt for Gemini story enhancement."""
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
        
        return f"""You are a creative story enhancement AI assistant specializing in enriching narratives through visual analysis.

TASK: Analyze the provided photo and enhance the user's story transcript with rich, immersive details.

ORIGINAL STORY:
"{transcript}"

LANGUAGE: {lang_name}

INSTRUCTIONS:
1. Carefully analyze the uploaded photo for:
   - Visual elements (colors, objects, people, scenery)
   - Mood and atmosphere 
   - Setting details and environment
   - Any narrative possibilities the image suggests

2. Enhance the original story by incorporating:
   - Richer descriptive language inspired by the photo
   - Atmospheric details that match the visual mood
   - Character development with specific traits
   - Improved plot structure and pacing
   - Sensory details (sights, sounds, textures, etc.)

3. Keep the core narrative intact while making it more engaging and vivid

4. Generate specific insights about what improvements were made

IMPORTANT: 
- Maintain the original story's essence and intent
- Respond in {lang_name}
- Keep enhancements appropriate for all audiences
- Focus on literary quality and immersive storytelling

OUTPUT FORMAT (valid JSON):
```json
{{
  "enhanced_transcript": "Your enhanced story here with rich details...",
  "insights": {{
    "plot": "Explanation of plot improvements made",
    "character": "Character development enhancements", 
    "setting": "Setting and atmosphere improvements",
    "mood": "Tone and mood enhancements based on the photo"
  }}
}}
```"""
    
    def _parse_response(self, response: Dict[str, Any]) -> GeminiResponse:
        """Parse and validate Gemini API response."""
        required_fields = ["enhanced_transcript", "insights"]
        
        for field in required_fields:
            if field not in response:
                raise GeminiError(f"Invalid response format: missing '{field}' field")
        
        # Validate insights structure
        insights = response.get("insights", {})
        if not isinstance(insights, dict):
            raise GeminiError("Invalid response format: 'insights' must be an object")
        
        return GeminiResponse(
            enhanced_transcript=response["enhanced_transcript"],
            insights=insights
        )