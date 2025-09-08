"""
Google OAuth authentication service for verifying ID tokens from iOS client.
"""
import logging
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import UserProfile
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import requests

logger = logging.getLogger(__name__)


class GoogleAuthError(Exception):
    """Custom exception for Google authentication errors."""
    pass


class GoogleAuthService:
    """Google OAuth service for ID token verification and user management."""
    
    # Google's public key endpoints
    GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
    GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"
    
    def __init__(self):
        self.google_certs = None
        self._load_google_certs()
    
    def _load_google_certs(self):
        """Load Google's public certificates for JWT verification."""
        try:
            response = requests.get(self.GOOGLE_CERTS_URL, timeout=10)
            response.raise_for_status()
            self.google_certs = response.json()
            logger.info("✅ Google certificates loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load Google certificates: {e}")
            self.google_certs = None
    
    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verify Google ID token and extract user information.
        
        Args:
            id_token: Google ID token from iOS client
            
        Returns:
            Dict containing verified user information
            
        Raises:
            GoogleAuthError: If token verification fails
        """
        if not id_token or not id_token.strip():
            raise GoogleAuthError("ID token is required")
        
        try:
            # First, try to decode without verification for development
            if settings.debug:
                return await self._verify_token_debug(id_token)
            
            # Production: Verify with Google's certificates
            return await self._verify_token_production(id_token)
            
        except Exception as e:
            logger.error(f"❌ ID token verification failed: {e}")
            raise GoogleAuthError(f"Invalid ID token: {str(e)}")
    
    async def _verify_token_debug(self, id_token: str) -> Dict[str, Any]:
        """Debug verification - validate with Google's tokeninfo endpoint."""
        try:
            response = requests.get(
                f"{self.GOOGLE_TOKEN_INFO_URL}?id_token={id_token}",
                timeout=10
            )
            
            if response.status_code != 200:
                raise GoogleAuthError("Invalid token")
            
            token_info = response.json()
            
            # Validate required fields
            if 'email' not in token_info:
                raise GoogleAuthError("Token missing email")
            
            if 'sub' not in token_info:
                raise GoogleAuthError("Token missing subject")
            
            logger.info(f"✅ Token verified for user: {token_info.get('email')}")
            return token_info
            
        except requests.RequestException as e:
            logger.error(f"❌ Google tokeninfo API error: {e}")
            raise GoogleAuthError("Failed to verify token with Google")
    
    async def _verify_token_production(self, id_token: str) -> Dict[str, Any]:
        """Production verification using Google's public certificates."""
        if not self.google_certs:
            self._load_google_certs()
            
        if not self.google_certs:
            raise GoogleAuthError("Google certificates not available")
        
        try:
            # Decode header to get key ID
            unverified_header = jwt.get_unverified_header(id_token)
            key_id = unverified_header.get("kid")
            
            if not key_id or key_id not in self.google_certs.get("keys", {}):
                raise GoogleAuthError("Invalid key ID in token")
            
            # Get the public key
            key_data = None
            for key in self.google_certs["keys"]:
                if key["kid"] == key_id:
                    key_data = key
                    break
            
            if not key_data:
                raise GoogleAuthError("Public key not found")
            
            # Verify and decode the token
            payload = jwt.decode(
                id_token,
                key_data,
                algorithms=["RS256"],
                audience=settings.google_oauth_client_id,
                issuer="https://accounts.google.com"
            )
            
            logger.info(f"✅ Token verified for user: {payload.get('email')}")
            return payload
            
        except JWTError as e:
            raise GoogleAuthError(f"JWT verification failed: {str(e)}")
    
    async def get_or_create_user(self, token_info: Dict[str, Any], db: Session) -> User:
        """
        Get existing user or create new user from Google token information.
        
        Args:
            token_info: Verified token payload from Google
            db: Database session
            
        Returns:
            User model instance
        """
        google_id = token_info["sub"]
        email = token_info["email"]
        name = token_info.get("name")
        picture = token_info.get("picture")
        
        try:
            # Check if user already exists by Google ID
            existing_user = db.query(User).filter(User.google_id == google_id).first()
            
            if existing_user:
                # Update last login and any changed information
                existing_user.last_login = datetime.now(timezone.utc)
                if name and existing_user.name != name:
                    existing_user.name = name
                if picture and existing_user.picture != picture:
                    existing_user.picture = picture
                
                db.commit()
                db.refresh(existing_user)
                
                logger.info(f"✅ Existing user logged in: {email}")
                return existing_user
            
            # Check if user exists with same email but different Google ID
            # This handles cases where user might have multiple Google accounts
            existing_by_email = db.query(User).filter(User.email == email).first()
            if existing_by_email:
                # Update the existing user's Google ID
                existing_by_email.google_id = google_id
                existing_by_email.last_login = datetime.now(timezone.utc)
                if name:
                    existing_by_email.name = name
                if picture:
                    existing_by_email.picture = picture
                
                db.commit()
                db.refresh(existing_by_email)
                
                logger.info(f"✅ User updated with new Google ID: {email}")
                return existing_by_email
            
            # Create new user
            new_user = User(
                user_id=f"usr_{google_id[:12]}",  # Create internal user ID
                email=email,
                name=name,
                picture=picture,
                google_id=google_id,
                last_login=datetime.now(timezone.utc)
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            logger.info(f"✅ New user created: {email}")
            return new_user
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to get/create user: {e}")
            raise GoogleAuthError("Failed to process user data")
    
    def generate_jwt_token(self, user: User) -> str:
        """
        Generate JWT token for authenticated user.
        
        Args:
            user: User model instance
            
        Returns:
            JWT token string
        """
        try:
            from datetime import timedelta
            
            # Token payload
            payload = {
                "sub": user.user_id,  # Subject (user ID)
                "email": user.email,
                "name": user.name,
                "iat": datetime.now(timezone.utc),
                "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
            }
            
            # Generate JWT token
            token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
            
            logger.info(f"✅ JWT token generated for user: {user.email}")
            return token
            
        except Exception as e:
            logger.error(f"❌ Failed to generate JWT token: {e}")
            raise GoogleAuthError("Failed to generate authentication token")
    
    def create_user_profile(self, user: User) -> UserProfile:
        """
        Create UserProfile response from User model.
        
        Args:
            user: User model instance
            
        Returns:
            UserProfile schema instance
        """
        return UserProfile(
            user_id=user.user_id,
            email=user.email,
            name=user.name,
            picture=user.picture
        )
    
    async def test_service(self) -> bool:
        """Test if the Google Auth service is working."""
        try:
            # Test loading Google certificates
            self._load_google_certs()
            return self.google_certs is not None
        except Exception as e:
            logger.error(f"Google Auth service test failed: {e}")
            return False