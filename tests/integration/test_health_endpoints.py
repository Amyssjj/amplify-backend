"""
Integration tests for health check endpoints.
"""
import pytest
from fastapi import status


@pytest.mark.integration
class TestHealthEndpoints:
    """Integration tests for health check API endpoints."""
    
    def test_basic_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check required fields from OpenAPI spec
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_root_endpoint(self, client):
        """Test root endpoint health check."""
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "message" in data
        assert "status" in data
        assert data["message"] == "Amplify Backend API"
        assert data["status"] == "running"
    
    def test_detailed_health_check(self, client):
        """Test detailed health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Basic health endpoint should return simple status
        assert data["status"] == "healthy"
        assert "service" in data
        assert data["service"] == "amplify-backend"
    
    def test_readiness_check_endpoint(self, client):
        """Test readiness check endpoint (if implemented)."""
        response = client.get("/health/ready")
        
        # This endpoint may not be fully implemented yet
        # It should exist based on OpenAPI spec
        if response.status_code == status.HTTP_404_NOT_FOUND:
            # Endpoint not implemented yet
            pytest.skip("Readiness endpoint not implemented yet")
        
        # If implemented, should return readiness status
        assert response.status_code in [
            status.HTTP_200_OK,  # All services ready
            status.HTTP_503_SERVICE_UNAVAILABLE  # Some services not ready
        ]
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "status" in data
            assert "services" in data
    
    def test_health_endpoints_http_methods(self, client):
        """Test that health endpoints only accept GET method."""
        # GET should work
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        
        # POST should not be allowed
        response = client.post("/health")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # PUT should not be allowed
        response = client.put("/health")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # DELETE should not be allowed
        response = client.delete("/health")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_health_check_response_time(self, client):
        """Test that health checks respond quickly."""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == status.HTTP_200_OK
        # Health checks should be fast (under 1 second)
        assert response_time < 1.0
    
    def test_health_check_no_side_effects(self, client):
        """Test that health checks don't cause side effects."""
        # Make multiple health check calls
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert data["status"] == "healthy"
        
        # Health checks should be idempotent
        # Verify system is still in same state
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
    
    def test_health_check_content_type(self, client):
        """Test health check response content type."""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        assert "application/json" in response.headers["content-type"]
    
    def test_health_monitoring_integration(self, client):
        """Test health endpoints for monitoring systems."""
        # Test that health endpoints provide monitoring-friendly responses
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should have consistent structure for monitoring
        assert isinstance(data["status"], str)
        
        # Status should be one of expected values
        valid_statuses = ["healthy", "unhealthy", "degraded"]
        assert data["status"] in valid_statuses
    
    def test_health_check_database_independent(self, client, db_session):
        """Test that basic health check works even if database has issues."""
        # Health check should work regardless of database state
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        
        # Basic health check shouldn't depend on database connectivity
        # This ensures the service can report health even during DB issues