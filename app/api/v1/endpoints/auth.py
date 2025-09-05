"""
Authentication endpoints.
"""
from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import LoginRequest, Token

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