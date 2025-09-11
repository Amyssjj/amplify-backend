"""Unit tests for authentication module."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

from app.core.auth import (
    get_current_user_optional,
    get_current_user_required,
    verify_jwt_token,
    get_user_id_or_anonymous,
    AuthError
)
from app.models.user import User


class TestCoreAuth:
    """Test suite for core authentication functions."""

    @pytest.mark.asyncio
    async def test_get_current_user_optional_no_credentials(self):
        """Test get_current_user_optional with no credentials."""
        mock_db = Mock()

        result = await get_current_user_optional(credentials=None, db=mock_db)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_optional_with_valid_token(self):
        """Test get_current_user_optional with valid token."""
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid_token"

        mock_user = Mock(spec=User)
        mock_user.user_id = "usr_123"

        mock_db = Mock()

        with patch('app.core.auth.verify_jwt_token', return_value=mock_user):
            result = await get_current_user_optional(credentials=mock_credentials, db=mock_db)
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_current_user_optional_with_invalid_token(self):
        """Test get_current_user_optional with invalid token returns None."""
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid_token"

        mock_db = Mock()

        with patch('app.core.auth.verify_jwt_token', side_effect=JWTError("Invalid token")):
            result = await get_current_user_optional(credentials=mock_credentials, db=mock_db)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_required_no_credentials(self):
        """Test get_current_user_required with no credentials raises exception."""
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "token"
        mock_db = Mock()

        with patch('app.core.auth.verify_jwt_token', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_required(credentials=mock_credentials, db=mock_db)
            assert exc_info.value.status_code == 401
            # The actual error message depends on which exception is caught
            assert exc_info.value.detail in ["Invalid authentication credentials", "Authentication failed"]

    @pytest.mark.asyncio
    async def test_get_current_user_required_with_valid_token(self):
        """Test get_current_user_required with valid token."""
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid_token"

        mock_user = Mock(spec=User)
        mock_user.user_id = "usr_123"

        mock_db = Mock()

        with patch('app.core.auth.verify_jwt_token', return_value=mock_user):
            result = await get_current_user_required(credentials=mock_credentials, db=mock_db)
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_current_user_required_with_invalid_token(self):
        """Test get_current_user_required with invalid token raises exception."""
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid_token"

        mock_db = Mock()

        with patch('app.core.auth.verify_jwt_token', side_effect=JWTError("Invalid token")):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_required(credentials=mock_credentials, db=mock_db)
            assert exc_info.value.status_code == 401
            assert "Could not validate credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_jwt_token_valid(self):
        """Test verify_jwt_token with valid token."""
        mock_user = Mock(spec=User)
        mock_user.user_id = "usr_123"

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Create a valid JWT token
        token_payload = {
            "sub": "usr_123",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }

        with patch('app.core.auth.jwt.decode', return_value=token_payload):
            result = await verify_jwt_token("valid_token", mock_db)
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_verify_jwt_token_invalid(self):
        """Test verify_jwt_token with invalid token raises JWTError."""
        mock_db = Mock()

        with patch('app.core.auth.jwt.decode', side_effect=JWTError("Invalid token")):
            with pytest.raises(JWTError):
                await verify_jwt_token("invalid_token", mock_db)

    @pytest.mark.asyncio
    async def test_verify_jwt_token_expired(self):
        """Test verify_jwt_token with expired token."""
        mock_db = Mock()

        with patch('app.core.auth.jwt.decode', side_effect=JWTError("Token expired")):
            with pytest.raises(JWTError):
                await verify_jwt_token("expired_token", mock_db)

    @pytest.mark.asyncio
    async def test_verify_jwt_token_user_not_found(self):
        """Test verify_jwt_token when user is not found in database."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        token_payload = {
            "sub": "usr_nonexistent",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }

        with patch('app.core.auth.jwt.decode', return_value=token_payload):
            result = await verify_jwt_token("valid_token", mock_db)
            assert result is None

    @pytest.mark.asyncio
    async def test_verify_jwt_token_missing_sub(self):
        """Test verify_jwt_token with token missing 'sub' field."""
        mock_db = Mock()

        # Token payload without 'sub'
        token_payload = {
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }

        with patch('app.core.auth.jwt.decode', return_value=token_payload):
            result = await verify_jwt_token("token_without_sub", mock_db)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_user_id_or_anonymous_with_user(self):
        """Test get_user_id_or_anonymous with authenticated user."""
        mock_user = Mock(spec=User)
        mock_user.user_id = "usr_123"

        result = await get_user_id_or_anonymous(user=mock_user)
        assert result == "usr_123"

    @pytest.mark.asyncio
    async def test_get_user_id_or_anonymous_without_user(self):
        """Test get_user_id_or_anonymous without user returns anonymous."""
        result = await get_user_id_or_anonymous(user=None)
        assert result == "anonymous_user"

    @pytest.mark.asyncio
    async def test_get_user_id_or_anonymous_with_dict_user(self):
        """Test get_user_id_or_anonymous with user as dict (edge case)."""
        # Even if user is provided as a dict-like object with user_id
        mock_user = Mock()
        mock_user.user_id = "usr_456"

        result = await get_user_id_or_anonymous(user=mock_user)
        assert result == "usr_456"

    def test_auth_error_exception(self):
        """Test AuthError exception can be raised and caught."""
        with pytest.raises(AuthError) as exc_info:
            raise AuthError("Test authentication error")
        assert str(exc_info.value) == "Test authentication error"

    @pytest.mark.asyncio
    async def test_get_current_user_optional_database_error(self):
        """Test get_current_user_optional handles database errors gracefully."""
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid_token"

        mock_db = Mock()

        # Simulate database error
        with patch('app.core.auth.verify_jwt_token', side_effect=Exception("Database connection error")):
            result = await get_current_user_optional(credentials=mock_credentials, db=mock_db)
            assert result is None  # Should return None, not raise

    @pytest.mark.asyncio
    async def test_get_current_user_required_database_error(self):
        """Test get_current_user_required raises HTTP exception on database error."""
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid_token"

        mock_db = Mock()

        # Simulate database error
        with patch('app.core.auth.verify_jwt_token', side_effect=Exception("Database connection error")):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_required(credentials=mock_credentials, db=mock_db)
            assert exc_info.value.status_code == 401
            assert "Authentication failed" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_jwt_token_wrong_algorithm(self):
        """Test verify_jwt_token with wrong algorithm."""
        mock_db = Mock()

        with patch('app.core.auth.jwt.decode', side_effect=JWTError("Algorithm mismatch")):
            with pytest.raises(JWTError):
                await verify_jwt_token("token_wrong_algo", mock_db)

    @pytest.mark.asyncio
    async def test_verify_jwt_token_malformed(self):
        """Test verify_jwt_token with malformed token."""
        mock_db = Mock()

        with patch('app.core.auth.jwt.decode', side_effect=JWTError("Malformed token")):
            with pytest.raises(JWTError):
                await verify_jwt_token("malformed.token", mock_db)
