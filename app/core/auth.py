"""
Authentication utilities and dependencies for FastAPI.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Optional

from app.core.config import settings
from app.core.database import get_db_session
from app.models.user import User

security = HTTPBearer(auto_error=False)


class AuthError(Exception):
    """Custom exception for authentication errors."""
    pass


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db_session)
) -> Optional[User]:
    """
    Get current user from JWT token (optional).
    Returns None if no token provided or invalid token.
    Used for endpoints that work both with and without authentication.
    """
    if not credentials:
        return None
    
    try:
        return await verify_jwt_token(credentials.credentials, db)
    except Exception:
        # Return None for optional auth - don't raise errors
        return None


async def get_current_user_required(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session)
) -> User:
    """
    Get current user from JWT token (required).
    Raises HTTP 401 if no token or invalid token.
    """
    try:
        user = await verify_jwt_token(credentials.credentials, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_jwt_token(token: str, db: Session) -> Optional[User]:
    """
    Verify JWT token and return user.
    
    Args:
        token: JWT token string
        db: Database session
        
    Returns:
        User model instance or None if invalid
        
    Raises:
        JWTError: If token is invalid
    """
    try:
        # Decode the JWT token
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            return None
        
        # Get user from database
        user = db.query(User).filter(User.user_id == user_id).first()
        return user
        
    except JWTError:
        raise
    except Exception:
        return None


def get_user_id_or_anonymous(current_user: Optional[User] = Depends(get_current_user_optional)) -> str:
    """
    Get user ID from authenticated user or return 'anonymous_user' for backwards compatibility.
    This is a transitional function while authentication is being rolled out.
    """
    if current_user:
        return current_user.user_id
    else:
        return "anonymous_user"