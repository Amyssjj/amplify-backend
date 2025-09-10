"""
Authentication endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.schemas.auth import LoginRequest, Token, GoogleAuthRequest, AuthResponse, UserProfile
from app.services.google_auth_service import GoogleAuthService, GoogleAuthError
from app.core.database import get_db_session
from app.core.config import settings

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
async def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db_session)):
    """Google OAuth authentication endpoint."""
    try:
        # Initialize Google Auth service
        google_auth_service = GoogleAuthService()

        # Verify the Google ID token
        token_info = await google_auth_service.verify_id_token(request.id_token)

        # Get or create user in database
        user = await google_auth_service.get_or_create_user(token_info, db)

        # Generate JWT token for the user
        jwt_token = google_auth_service.generate_jwt_token(user)

        # Create user profile response
        user_profile = google_auth_service.create_user_profile(user)

        return AuthResponse(
            access_token=jwt_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,  # 30 days in seconds
            user=user_profile
        )

    except GoogleAuthError as e:
        # Handle specific Google auth errors
        if "Invalid token" in str(e) or "Token missing" in str(e) or "ID token is required" in str(e):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid Google ID token"
            )
        elif "verification failed" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google authentication failed"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable"
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"❌ Google auth error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
