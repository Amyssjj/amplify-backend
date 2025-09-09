"""
OpenAI story enhancement service for analyzing photos and enhancing story transcripts.
"""
import os
import json
import re
from typing import Dict, Any, List
import openai
from app.services.ai_service_interface import AIStoryEnhancementService
from app.schemas.ai_response import AIResponse
from app.services.prompt_manager import prompt_manager


class OpenAIError(Exception):
    """Custom exception for OpenAI service errors."""
    pass


class OpenAIService(AIStoryEnhancementService):
    """Service for story enhancement using OpenAI's GPT models with optional vision capabilities."""

    def __init__(self, api_key: str = None, model: str = None):
        """Initialize OpenAI service with API configuration."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise OpenAIError(
                "OPENAI_API_KEY environment variable is required")

        # Set model with fallback to config default
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4-vision-preview")

        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.api_key)

        # Define vision-capable models
        self.vision_models = {"gpt-4-vision-preview", "gpt-4-turbo"}

    async def enhance_story_with_photo(self,
                                       photo_base64: str,
                                       transcript: str,
                                       language: str = "en") -> AIResponse:
        """
        Enhance a story transcript using photo analysis with OpenAI.

        Args:
            photo_base64: Base64 encoded image data
            transcript: Original story transcript
            language: Language code (ISO 639-1)

        Returns:
            AIResponse with enhanced transcript and insights

        Raises:
            OpenAIError: If validation fails or API call fails
        """
        try:
            # Validate inputs
            self._validate_inputs(photo_base64, transcript, language)

            # Call OpenAI API
            response = self._call_openai_api(photo_base64=photo_base64,
                                                   transcript=transcript,
                                                   language=language)

            # Validate and return response
            return self._parse_response(response)

        except Exception as e:
            if isinstance(e, OpenAIError):
                raise
            raise OpenAIError(f"OpenAI API error: {str(e)}")

    def supports_vision(self) -> bool:
        """Check if this service supports vision/image analysis."""
        return self.model in self.vision_models

    def get_provider_name(self) -> str:
        """Get the name of the AI provider."""
        return "openai"

    def _validate_inputs(self, photo_base64: str, transcript: str,
                         language: str) -> None:
        """Validate input parameters."""
        if not photo_base64 or not photo_base64.strip():
            raise OpenAIError("Photo data is required")

        if not transcript or not transcript.strip():
            raise OpenAIError("Transcript is required")

        if len(transcript) > 5000:
            raise OpenAIError("Transcript too long (max 5000 characters)")

        # Validate language code (ISO 639-1)
        valid_languages = {
            'en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'ko', 'zh', 'ru', 'ar',
            'hi'
        }
        if language not in valid_languages:
            raise OpenAIError(f"Invalid language code: {language}")

    def _call_openai_api(self, photo_base64: str, transcript: str,
                               language: str) -> Dict[str, Any]:
        """Make the actual API call to OpenAI."""
        try:
            # Build prompt using PromptManager
            prompt = self._build_prompt(transcript, language)

            # Build messages based on model capabilities
            messages = self._build_messages(prompt, photo_base64)

            # Generate content with OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
                response_format={"type": "json_object"} if self.supports_vision() else None
            )

            # Extract response text
            response_text = response.choices[0].message.content

            # Parse JSON response
            return self._extract_json_from_response(response_text)

        except json.JSONDecodeError as e:
            raise OpenAIError(f"Invalid JSON response from OpenAI: {str(e)}")
        except Exception as e:
            raise OpenAIError(f"OpenAI API call failed: {str(e)}")

    def _build_prompt(self, transcript: str, language: str) -> str:
        """Build the prompt for OpenAI story enhancement using PromptManager."""
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
            base_prompt = prompt_template.format(transcript=transcript,
                                          language_name=lang_name)

            # Add JSON format instruction for OpenAI
            json_instruction = "\n\nPlease respond with a valid JSON object containing 'enhanced_transcript' and 'insights' fields."
            return base_prompt + json_instruction

        except Exception as e:
            # Fallback to error message if prompt loading fails
            raise OpenAIError(f"Failed to load prompt template: {str(e)}")

    def _build_messages(self, prompt: str, photo_base64: str) -> List[Dict[str, Any]]:
        """Build messages for OpenAI API based on model capabilities."""
        if self.supports_vision():
            # Vision model: use multi-modal message format
            return [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{photo_base64}"
                            }
                        }
                    ]
                }
            ]
        else:
            # Text-only model: include image description request in text
            text_prompt = prompt + "\n\nNote: An image was provided but cannot be analyzed with this model. Please enhance the story based on the transcript alone."
            return [
                {
                    "role": "user",
                    "content": text_prompt
                }
            ]

    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON from OpenAI response, handling potential markdown formatting."""
        # First try to parse as-is (for JSON mode responses)
        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```',
                               response_text, re.DOTALL | re.MULTILINE)
        if json_match:
            json_str = json_match.group(1)
            return json.loads(json_str)

        # Try to find JSON object in the text
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))

        raise OpenAIError(f"Could not extract valid JSON from response: {response_text}")

    def _parse_response(self, response: Dict[str, Any]) -> AIResponse:
        """Parse and validate OpenAI API response."""
        required_fields = ["enhanced_transcript", "insights"]

        for field in required_fields:
            if field not in response:
                raise OpenAIError(
                    f"Invalid response format: missing '{field}' field")

        # Validate insights structure
        insights = response.get("insights", {})
        if not isinstance(insights, dict):
            raise OpenAIError(
                "Invalid response format: 'insights' must be an object")

        return AIResponse(
            enhanced_transcript=response["enhanced_transcript"],
            insights=insights)
