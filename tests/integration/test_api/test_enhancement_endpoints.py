"""
Integration tests for enhancement API endpoints.
"""
import pytest
from fastapi.testclient import TestClient


class TestEnhancementEndpoints:
    """Test cases for enhancement API endpoints."""
    
    def test_enhance_story_endpoint(self, client: TestClient, sample_enhancement_request: dict):
        """Test the story enhancement endpoint."""
        response = client.post("/api/v1/enhance/story", json=sample_enhancement_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "enhanced_story" in data
        assert "insights" in data
        assert "enhancement_id" in data
        assert "created_at" in data
        
        # Verify data types
        assert isinstance(data["enhanced_story"], str)
        assert isinstance(data["insights"], list)
        assert isinstance(data["enhancement_id"], str)
        assert isinstance(data["created_at"], str)
    
    def test_enhance_story_invalid_request(self, client: TestClient):
        """Test enhancement endpoint with invalid request."""
        response = client.post("/api/v1/enhance/story", json={})
        
        assert response.status_code == 422  # Validation error
    
    def test_enhancement_history_endpoint(self, client: TestClient):
        """Test the enhancement history endpoint."""
        response = client.get("/api/v1/enhance/history")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return a list (even if empty for now)
        assert isinstance(data, list)