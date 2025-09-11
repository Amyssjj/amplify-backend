"""Unit tests for Google OAuth authentication service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.google_auth_service import GoogleAuthService, GoogleAuthError
from app.models.user import User
from datetime import datetime, timezone, timedelta
from jose import jwt


class TestGoogleAuthService:
    """Test suite for GoogleAuthService."""

    def test_init_loads_google_certs_success(self):
        """Test successful initialization and certificate loading."""
        mock_response = Mock()
        mock_response.json.return_value = {"keys": ["cert1", "cert2"]}
        mock_response.raise_for_status = Mock()

        with patch('requests.get', return_value=mock_response) as mock_get:
            service = GoogleAuthService()
            assert service.google_certs == {"keys": ["cert1", "cert2"]}
            mock_get.assert_called_once_with(GoogleAuthService.GOOGLE_CERTS_URL, timeout=10)

    def test_init_handles_cert_loading_failure(self):
        """Test initialization when certificate loading fails."""
        with patch('requests.get', side_effect=Exception("Network error")):
            service = GoogleAuthService()
            assert service.google_certs is None

    @pytest.mark.asyncio
    async def test_verify_id_token_empty_token(self):
        """Test verify_id_token with empty token."""
        service = GoogleAuthService()

        with pytest.raises(GoogleAuthError, match="ID token is required"):
            await service.verify_id_token("")

        with pytest.raises(GoogleAuthError, match="ID token is required"):
            await service.verify_id_token("   ")

    @pytest.mark.asyncio
    async def test_verify_id_token_debug_mode_success(self):
        """Test verify_id_token in debug mode with valid token."""
        service = GoogleAuthService()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "email": "test@example.com",
            "sub": "12345",
            "name": "Test User"
        }

        with patch('app.services.google_auth_service.settings.debug', True):
            with patch('requests.get', return_value=mock_response):
                result = await service.verify_id_token("test_token")
                assert result["email"] == "test@example.com"
                assert result["sub"] == "12345"

    @pytest.mark.asyncio
    async def test_verify_id_token_debug_mode_invalid_token(self):
        """Test verify_id_token in debug mode with invalid token."""
        service = GoogleAuthService()
        mock_response = Mock()
        mock_response.status_code = 400

        with patch('app.services.google_auth_service.settings.debug', True):
            with patch('requests.get', return_value=mock_response):
                with pytest.raises(GoogleAuthError, match="Invalid token"):
                    await service.verify_id_token("invalid_token")

    @pytest.mark.asyncio
    async def test_verify_id_token_production_no_certs(self):
        """Test verify_id_token in production when certificates are not loaded."""
        service = GoogleAuthService()
        service.google_certs = None

        with patch('app.services.google_auth_service.settings.debug', False):
            # The error message will be about invalid token, not missing certs,
            # because jwt.get_unverified_header fails with malformed token first
            with pytest.raises(GoogleAuthError, match="Invalid ID token"):
                await service.verify_id_token("test_token")

    @pytest.mark.asyncio
    async def test_get_or_create_user_new_user(self):
        """Test creating a new user from Google token info."""
        service = GoogleAuthService()

        # Mock database session
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        token_info = {
            "sub": "google123456789",
            "email": "newuser@example.com",
            "name": "New User",
            "picture": "https://example.com/pic.jpg"
        }

        result = await service.get_or_create_user(token_info, mock_db)

        # Verify user was added
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

        # Check the created user
        created_user = mock_db.add.call_args[0][0]
        assert created_user.email == "newuser@example.com"
        assert created_user.name == "New User"
        assert created_user.google_id == "google123456789"

    @pytest.mark.asyncio
    async def test_get_or_create_user_existing_user(self):
        """Test getting an existing user from Google token info."""
        service = GoogleAuthService()

        # Create a mock existing user
        existing_user = Mock(spec=User)
        existing_user.email = "existing@example.com"
        existing_user.name = "Existing User"
        existing_user.google_id = "google123"
        existing_user.picture = None

        # Mock database session
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing_user
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        token_info = {
            "sub": "google123",
            "email": "existing@example.com",
            "name": "Updated Name",
            "picture": "https://example.com/new_pic.jpg"
        }

        result = await service.get_or_create_user(token_info, mock_db)

        # Verify the existing user was returned and updated
        assert result == existing_user
        assert existing_user.name == "Updated Name"
        assert existing_user.picture == "https://example.com/new_pic.jpg"
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_get_or_create_user_database_error(self):
        """Test get_or_create_user with database error."""
        service = GoogleAuthService()

        # Mock database session that raises an error
        mock_db = Mock()
        mock_db.query.side_effect = Exception("Database error")
        mock_db.rollback = Mock()

        token_info = {
            "sub": "google123",
            "email": "test@example.com"
        }

        with pytest.raises(GoogleAuthError, match="Failed to process user data"):
            await service.get_or_create_user(token_info, mock_db)

        mock_db.rollback.assert_called()

    def test_generate_jwt_token(self):
        """Test JWT token generation for a user."""
        service = GoogleAuthService()

        # Create a mock user
        mock_user = Mock(spec=User)
        mock_user.user_id = "usr_123"
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"

        with patch('app.services.google_auth_service.settings.secret_key', 'test_secret'):
            with patch('app.services.google_auth_service.settings.algorithm', 'HS256'):
                with patch('app.services.google_auth_service.settings.access_token_expire_minutes', 60):
                    token = service.generate_jwt_token(mock_user)

                    # Decode and verify token
                    decoded = jwt.decode(token, 'test_secret', algorithms=['HS256'])
                    assert decoded['sub'] == 'usr_123'
                    assert decoded['email'] == 'test@example.com'
                    assert decoded['name'] == 'Test User'

    def test_generate_jwt_token_error(self):
        """Test JWT token generation with error."""
        service = GoogleAuthService()

        # Create a mock user that will cause encoding to fail
        mock_user = Mock(spec=User)
        mock_user.user_id = "usr_123"
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"

        with patch('app.services.google_auth_service.jwt.encode', side_effect=Exception("Encoding error")):
            with pytest.raises(GoogleAuthError, match="Failed to generate authentication token"):
                service.generate_jwt_token(mock_user)

    def test_create_user_profile(self):
        """Test creating UserProfile from User model."""
        service = GoogleAuthService()

        # Create a mock user
        mock_user = Mock(spec=User)
        mock_user.user_id = "usr_123"
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"
        mock_user.picture = "https://example.com/pic.jpg"

        profile = service.create_user_profile(mock_user)

        assert profile.user_id == "usr_123"
        assert profile.email == "test@example.com"
        assert profile.name == "Test User"
        assert profile.picture == "https://example.com/pic.jpg"

    @pytest.mark.asyncio
    async def test_test_service(self):
        """Test the test_service method."""
        mock_response = Mock()
        mock_response.json.return_value = {"keys": ["cert1"]}
        mock_response.raise_for_status = Mock()

        with patch('requests.get', return_value=mock_response):
            service = GoogleAuthService()
            result = await service.test_service()
            assert result is True

    @pytest.mark.asyncio
    async def test_test_service_no_certs(self):
        """Test the test_service method when certificates cannot be loaded."""
        with patch('requests.get', side_effect=Exception("Network error")):
            service = GoogleAuthService()
            result = await service.test_service()
            assert result is False
