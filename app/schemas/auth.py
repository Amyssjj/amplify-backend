"""
Authentication-related schemas matching OpenAPI specification.
Google OAuth only - no username/password authentication.
"""
from pydantic import BaseModel, Field
from typing import Optional


class GoogleAuthRequest(BaseModel):
    """Google OAuth authentication request."""
    id_token: str = Field(..., description="Google ID token obtained from the iOS client")


class UserProfile(BaseModel):
    """User profile information from Google OAuth."""
    user_id: str = Field(..., description="Unique internal user ID")
    email: str = Field(..., description="User's email address")
    name: Optional[str] = Field(None, description="User's full name from Google")
    picture: Optional[str] = Field(None, description="URL to user's profile picture from Google")


class AuthResponse(BaseModel):
    """Authentication response with JWT token."""
    access_token: str = Field(..., description="The JWT token for authenticating subsequent API requests")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(3600, description="Token expiry time in seconds")
    user: UserProfile = Field(..., description="User profile information")
