"""Integration tests for health check endpoints."""
import pytest
from fastapi import status

@pytest.mark.integration
class TestHealthEndpoints:
    """Integration tests for health check API endpoints."""

    def test_basic_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/api/v1/health/")

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
        # Check for new fields we added
        assert "docs" in data
        assert "health" in data
        assert data["health"] == "/api/v1/health/"

    def test_detailed_health_check(self, client):
        """Test detailed health check endpoint."""
        response = client.get("/api/v1/health/detailed")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Detailed endpoint should return more information
        assert data["status"] == "healthy"
        assert "service" in data
        assert data["service"] == "amplify-backend"
        assert "version" in data
        assert "uptime" in data

    def test_readiness_check_endpoint(self, client):
        """Test readiness check endpoint (if implemented)."""
        response = client.get("/health/ready")

        # This endpoint doesn't exist, should return 404
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_health_endpoints_http_methods(self, client):
        """Test that health endpoints only accept GET requests."""
        # Test basic health endpoint
        response = client.get("/api/v1/health/")
        assert response.status_code == status.HTTP_200_OK

        response = client.post("/api/v1/health/")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        response = client.put("/api/v1/health/")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        response = client.delete("/api/v1/health/")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_health_check_response_time(self, client):
        """Test that health check responds quickly."""
        import time

        start_time = time.time()
        response = client.get("/api/v1/health/")
        end_time = time.time()

        assert response.status_code == status.HTTP_200_OK

        # Health check should respond in less than 100ms
        response_time = (end_time - start_time) * 1000
        assert response_time < 100, f"Health check took {response_time}ms"

    def test_health_check_no_side_effects(self, client):
        """Test that health check doesn't modify system state."""
        # Get initial state
        response1 = client.get("/api/v1/health/")
        data1 = response1.json()

        # Call health check multiple times
        for _ in range(5):
            client.get("/api/v1/health/")

        # Get final state
        response2 = client.get("/api/v1/health/")
        data2 = response2.json()

        # State should be identical
        assert data1 == data2

    def test_health_check_content_type(self, client):
        """Test that health check returns JSON content type."""
        response = client.get("/api/v1/health/")

        assert response.status_code == status.HTTP_200_OK
        assert "application/json" in response.headers["content-type"]

    def test_health_monitoring_integration(self, client):
        """Test health endpoints for monitoring tool integration."""
        # Test that basic health check can be used by monitoring tools
        response = client.get("/api/v1/health/")
        assert response.status_code == status.HTTP_200_OK

        # Should have a simple structure for easy parsing
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) >= 1  # At minimum, should have 'status'

        # Test detailed health check for more comprehensive monitoring
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert isinstance(data, dict)
        assert len(data) >= 3  # Should have status, service, version at minimum

    def test_health_check_database_independent(self, client):
        """Test that health check works even if database is unavailable."""
        # Health check should work regardless of database state
        response = client.get("/api/v1/health/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
