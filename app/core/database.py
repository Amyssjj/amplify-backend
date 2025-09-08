"""
Database initialization and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from app.models.base import Base
from app.core.config import settings


def get_database_url() -> str:
    """Get database URL from environment or settings."""
    database_url = os.getenv("DATABASE_URL") or settings.database_url
    
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    # Fix for Replit/Heroku postgres URLs
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    return database_url


def create_database_engine():
    """Create database engine."""
    database_url = get_database_url()
    return create_engine(database_url, echo=settings.debug)


def create_tables():
    """Create all database tables."""
    try:
        database_url = get_database_url()
        engine = create_engine(database_url)
        
        # Import all models to ensure they are registered with Base
        from app.models import Enhancement, User
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Create anonymous user for testing before auth is implemented
        create_anonymous_user(engine)
        
        print("✅ Database tables created successfully")
        
    except Exception as e:
        print(f"❌ Failed to create database tables: {e}")
        raise


def create_anonymous_user(engine):
    """Create an anonymous user for testing purposes."""
    try:
        from sqlalchemy.orm import sessionmaker
        from app.models.user import User
        
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Check if anonymous user already exists
        existing_user = session.query(User).filter(User.user_id == "anonymous_user").first()
        
        if not existing_user:
            anonymous_user = User(
                user_id="anonymous_user",
                email="anonymous@example.com",
                name="Anonymous User",
                google_id="anonymous_google_id"
            )
            session.add(anonymous_user)
            session.commit()
            print("✅ Anonymous user created successfully")
        else:
            print("ℹ️  Anonymous user already exists")
            
        session.close()
        
    except Exception as e:
        print(f"⚠️ Failed to create anonymous user: {e}")
        # Don't fail the entire setup if this fails


def get_db_session():
    """Get database session dependency for FastAPI."""
    try:
        database_url = get_database_url()
        engine = create_engine(database_url, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
            
    except ValueError as e:
        if "DATABASE_URL environment variable is required" in str(e):
            print(f"❌ Database session error: Database not configured")
            raise RuntimeError("Database not configured") from e
        print(f"❌ Database session error: {e}")
        raise
    except Exception as e:
        print(f"❌ Database session error: {e}")
        raise


# Initialize on module import for Replit
if __name__ == "__main__":
    create_tables()