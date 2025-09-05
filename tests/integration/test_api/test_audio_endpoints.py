"""
Integration tests for audio API endpoints.
"""
import pytest
from fastapi.testclient import TestClient


class TestAudioEndpoints:
    """Test cases for audio API endpoints."""
    
    def test_generate_audio_endpoint(self, client: TestClient, sample_audio_request: dict):
        """Test the audio generation endpoint."""
        response = client.post("/api/v1/audio/generate", json=sample_audio_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "audio_url" in data
        assert "duration" in data
        
        # Verify data types
        assert isinstance(data["audio_url"], str)
        assert isinstance(data["duration"], (int, float))
    
    def test_generate_audio_invalid_request(self, client: TestClient):
        """Test audio generation endpoint with invalid request."""
        response = client.post("/api/v1/audio/generate", json={})
        
        assert response.status_code == 422  # Validation error
    
    def test_get_voices_endpoint(self, client: TestClient):
        """Test the get voices endpoint."""
        response = client.get("/api/v1/audio/voices")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "voices" in data
        assert isinstance(data["voices"], list)
        
        # If voices exist, verify their structure
        if data["voices"]:
            voice = data["voices"][0]
            assert "id" in voice
            assert "name" in voice
            assert "language" in voice
            assert "gender" in voice