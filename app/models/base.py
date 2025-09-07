"""
Base database model configuration.
"""
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Database base class
Base = declarative_base()

# Database engine and session configuration
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Fix for Replit/Heroku postgres URLs
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    # Development fallback
    engine = None
    SessionLocal = None

def get_db():
    """Dependency to get database session."""
    if SessionLocal is None:
        raise RuntimeError("Database not configured. Set DATABASE_URL environment variable.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()