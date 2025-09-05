"""
End-to-end tests for complete user flows.
"""
import pytest
from fastapi.testclient import TestClient


class TestFullEnhancementFlow:
    """Test cases for complete enhancement user flows."""
    
    def test_complete_story_enhancement_flow(self, client: TestClient):
        """Test the complete flow from story submission to enhancement retrieval."""
        # Step 1: Submit a story for enhancement
        enhancement_request = {
            "story_text": "Once upon a time, there was a brave knight who ventured into the dark forest.",
            "enhancement_type": "plot"
        }
        
        response = client.post("/api/v1/enhance/story", json=enhancement_request)
        assert response.status_code == 200
        
        enhancement_data = response.json()
        enhancement_id = enhancement_data["enhancement_id"]
        
        # Verify the enhancement was created
        assert enhancement_id is not None
        assert len(enhancement_data["enhanced_story"]) > 0
        
        # Step 2: Check enhancement history (would include our new enhancement in real implementation)
        history_response = client.get("/api/v1/enhance/history")
        assert history_response.status_code == 200
        
        # Step 3: Generate audio for the enhanced story
        audio_request = {
            "text": enhancement_data["enhanced_story"][:100],  # Truncate for testing
            "voice_id": "voice-1",
            "speed": 1.0
        }
        
        audio_response = client.post("/api/v1/audio/generate", json=audio_request)
        assert audio_response.status_code == 200
        
        audio_data = audio_response.json()
        assert "audio_url" in audio_data
        assert "duration" in audio_data
    
    def test_authenticated_enhancement_flow(self, client: TestClient):
        """Test enhancement flow with authentication."""
        # Step 1: Login to get access token
        login_request = {
            "username": "demo",
            "password": "demo"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_request)
        assert login_response.status_code == 200
        
        token_data = login_response.json()
        access_token = token_data["access_token"]
        
        # Step 2: Use token for authenticated enhancement (if authentication is required)
        headers = {"Authorization": f"Bearer {access_token}"}
        
        enhancement_request = {
            "story_text": "A tale of adventure and discovery in distant lands.",
            "enhancement_type": "character"
        }
        
        # Note: Current implementation doesn't require auth, but structure is ready
        response = client.post("/api/v1/enhance/story", json=enhancement_request, headers=headers)
        assert response.status_code == 200