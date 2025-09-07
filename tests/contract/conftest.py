"""
Contract test configuration and fixtures.
"""
import pytest
from unittest.mock import patch, AsyncMock
from app.services.gemini_service import GeminiResponse


@pytest.fixture(autouse=True)
def mock_gemini_for_contract():
    """Automatically mock Gemini service for all contract tests."""
    with patch('app.api.v1.endpoints.enhancement.GeminiService') as mock_gemini_class:
        mock_gemini_instance = AsyncMock()
        mock_gemini_class.return_value = mock_gemini_instance
        
        # Contract-compliant mock response
        mock_response = GeminiResponse(
            enhanced_transcript="Once upon a time, in a mystical kingdom shrouded by ancient magic, there lived Sir Gareth the Bold, a brave knight of unwavering courage and noble heart.",
            insights={
                "plot": "Enhanced the basic quest narrative with specific magical conflict and clear stakes for the kingdom's salvation",
                "character": "Added character name (Sir Gareth the Bold), personality traits (unwavering courage, noble heart), and deeper motivation",
                "setting": "Incorporated mystical elements and ancient magic to transform the setting into a rich fantasy realm",
                "mood": "Elevated from simple adventure story to epic fantasy tale with dramatic stakes and heroic grandeur"
            }
        )
        mock_gemini_instance.enhance_story_with_photo.return_value = mock_response
        yield mock_gemini_class