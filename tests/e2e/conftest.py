"""
E2E test configuration and fixtures.
"""
import pytest
from unittest.mock import patch, AsyncMock
from app.services.gemini_service import GeminiResponse


@pytest.fixture(autouse=True)
def mock_gemini_for_e2e():
    """Automatically mock Gemini service for all E2E tests."""
    with patch('app.api.v1.endpoints.enhancement.GeminiService') as mock_gemini_class:
        mock_gemini_instance = AsyncMock()
        mock_gemini_class.return_value = mock_gemini_instance
        
        # Standard mock response for E2E tests
        mock_response = GeminiResponse(
            enhanced_transcript="In a mystical realm veiled by ancient magic, Sir Gareth the Brave, a noble knight of extraordinary courage, embarked upon a legendary quest to break the dark curse that had befallen his beloved kingdom.",
            insights={
                "plot": "Transformed basic quest into epic fantasy adventure with specific magical conflict",
                "character": "Enhanced protagonist with noble title, personality traits, and emotional stakes", 
                "setting": "Added mystical realm with ancient magic to create immersive fantasy world",
                "mood": "Elevated from simple story to grand epic with dramatic gravitas"
            }
        )
        mock_gemini_instance.enhance_story_with_photo.return_value = mock_response
        yield mock_gemini_class