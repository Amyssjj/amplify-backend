"""
User database model for Google OAuth authentication.
"""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import Base


class User(Base):
    """User table for Google OAuth authentication."""
    __tablename__ = "users"
    
    # Primary key - internal user ID
    user_id = Column(String, primary_key=True)
    
    # Google OAuth data (from AuthResponse schema)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    picture = Column(String, nullable=True)  # URL to profile picture
    
    # Google-specific fields
    google_id = Column(String, unique=True, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    enhancements = relationship("Enhancement", back_populates="user")