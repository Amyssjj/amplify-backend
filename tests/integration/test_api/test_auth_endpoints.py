"""
Integration tests for authentication API endpoints.
"""
import pytest
from fastapi.testclient import TestClient


class TestAuthEndpoints:
    """Test cases for authentication API endpoints."""
    
    def test_login_valid_credentials(self, client: TestClient, sample_login_request: dict):
        """Test login with valid credentials."""
        response = client.post("/api/v1/auth/login", json=sample_login_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        
        # Verify data types and values
        assert isinstance(data["access_token"], str)
        assert data["token_type"] == "bearer"
        assert isinstance(data["expires_in"], int)
        assert len(data["access_token"]) > 0
    
    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials."""
        invalid_request = {
            "username": "invalid",
            "password": "invalid"
        }
        
        response = client.post("/api/v1/auth/login", json=invalid_request)
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_login_missing_fields(self, client: TestClient):
        """Test login with missing required fields."""
        response = client.post("/api/v1/auth/login", json={})
        
        assert response.status_code == 422  # Validation error