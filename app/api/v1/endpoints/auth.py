"""
Authentication endpoints.
"""
from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import LoginRequest, Token, GoogleAuthRequest, AuthResponse, UserProfile

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """User login endpoint."""
    try:
        # TODO: Implement actual authentication logic
        # This is a placeholder response
        if request.username == "demo" and request.password == "demo":
            return Token(
                access_token="demo-token-123",
                token_type="bearer",
                expires_in=3600
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/google", response_model=AuthResponse)
async def google_auth(request: GoogleAuthRequest):
    """Google OAuth authentication endpoint."""
    try:
        # TODO: Implement Google ID token verification
        # For now, accept any non-empty token as valid for testing
        
        if not request.id_token or len(request.id_token.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid Google token"
            )
        
        # Placeholder response - would normally verify token with Google
        user_profile = UserProfile(
            user_id="usr_google_test123",
            email="test@google.com",
            name="Test User",
            picture="https://example.com/avatar.jpg"
        )
        
        return AuthResponse(
            access_token="google-jwt-token-placeholder",
            token_type="bearer",
            expires_in=3600,
            user=user_profile
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))