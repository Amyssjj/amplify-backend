"""
Integration tests for health check API endpoints.
"""
import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test cases for health check API endpoints."""
    
    def test_basic_health_check(self, client: TestClient):
        """Test the basic health check endpoint."""
        response = client.get("/api/v1/health/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "status" in data
        assert "service" in data
        
        # Verify values
        assert data["status"] == "healthy"
        assert data["service"] == "amplify-backend"
    
    def test_detailed_health_check(self, client: TestClient):
        """Test the detailed health check endpoint."""
        response = client.get("/api/v1/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "uptime" in data
        
        # Verify values
        assert data["status"] == "healthy"
        assert data["service"] == "amplify-backend"
        assert data["version"] == "1.0.0"
    
    def test_root_health_check(self, client: TestClient):
        """Test the root health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"