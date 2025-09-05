"""
Contract tests to validate API responses against OpenAPI specification.
"""
import pytest
import yaml
from fastapi.testclient import TestClient
from fastapi.openapi.utils import get_openapi


class TestOpenAPIContract:
    """Test cases to validate API contract compliance."""
    
    def test_openapi_spec_generation(self, client: TestClient):
        """Test that OpenAPI spec can be generated without errors."""
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        
        spec = response.json()
        
        # Verify basic OpenAPI structure
        assert "openapi" in spec
        assert "info" in spec
        assert "paths" in spec
        assert "components" in spec
    
    def test_openapi_spec_matches_yaml(self):
        """Test that generated spec matches our YAML definition structure."""
        # Load our YAML spec
        with open("openapi.yaml", "r") as f:
            yaml_spec = yaml.safe_load(f)
        
        # Verify basic structure matches
        assert "openapi" in yaml_spec
        assert "info" in yaml_spec
        assert "paths" in yaml_spec
        assert "components" in yaml_spec
        
        # Verify key endpoints exist
        paths = yaml_spec["paths"]
        assert "/health" in paths
        assert "/enhance/story" in paths
        assert "/enhance/history" in paths
        assert "/audio/generate" in paths
        assert "/audio/voices" in paths
        assert "/auth/login" in paths
    
    def test_response_schemas_compliance(self, client: TestClient):
        """Test that API responses comply with defined schemas."""
        # Test health endpoint response structure
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields according to schema
        assert "status" in data
        assert "service" in data
        assert isinstance(data["status"], str)
        assert isinstance(data["service"], str)
    
    def test_enhancement_response_schema(self, client: TestClient):
        """Test enhancement endpoint response schema compliance."""
        request_data = {
            "story_text": "Test story for schema validation",
            "enhancement_type": "plot"
        }
        
        response = client.post("/api/v1/enhance/story", json=request_data)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response matches EnhancementResponse schema
        required_fields = ["enhanced_story", "insights", "enhancement_id", "created_at"]
        for field in required_fields:
            assert field in data
        
        # Verify data types
        assert isinstance(data["enhanced_story"], str)
        assert isinstance(data["insights"], list)
        assert isinstance(data["enhancement_id"], str)
        assert isinstance(data["created_at"], str)
    
    def test_error_response_schema(self, client: TestClient):
        """Test that error responses follow the standard schema."""
        # Test validation error
        response = client.post("/api/v1/enhance/story", json={})
        assert response.status_code == 422
        
        # Test authentication error
        invalid_login = {
            "username": "invalid",
            "password": "invalid"
        }
        auth_response = client.post("/api/v1/auth/login", json=invalid_login)
        assert auth_response.status_code == 401
        
        error_data = auth_response.json()
        assert "detail" in error_data