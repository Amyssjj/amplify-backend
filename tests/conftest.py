"""
Global pytest fixtures for all tests.
"""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import asyncio
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os
import sys
import base64
import uuid

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from app.models.base import Base
from app.core.database import get_db_session

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_db():
    """Create test database with isolation per test."""

    # Use unique temporary database for each test
    temp_dir = tempfile.gettempdir()
    db_name = f"test_{uuid.uuid4().hex[:8]}.db"
    db_url = f"sqlite:///{temp_dir}/{db_name}"

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    yield TestingSessionLocal

    # Cleanup
    engine.dispose()
    try:
        os.unlink(f"{temp_dir}/{db_name}")
    except FileNotFoundError:
        pass


@pytest.fixture
def db_session(test_db):
    """Create database session for testing."""
    session = test_db()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(test_db) -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    def override_get_db():
        try:
            db = test_db()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db_session] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(test_db) -> AsyncClient:
    """Create an async test client for the FastAPI app."""
    def override_get_db():
        try:
            db = test_db()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db_session] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as async_test_client:
        yield async_test_client

    app.dependency_overrides.clear()


# Sample data fixtures matching OpenAPI specification
@pytest.fixture
def sample_enhancement_request() -> dict:
    """Sample enhancement request matching OpenAPI schema."""
    # Create a simple 1x1 pixel PNG in base64
    sample_image = base64.b64encode(
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x01\x00\x00\x00\x007n\xf9$\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\r\n\x1d\xb3\x00\x00\x00\x00IEND\xaeB`\x82'
    ).decode('utf-8')

    return {
        "photo_base64": sample_image,
        "transcript": "Once upon a time, there was a brave knight who embarked on a quest to save the kingdom.",
        "language": "en"
    }


@pytest.fixture
def sample_google_auth_request() -> dict:
    """Sample Google OAuth request."""
    return {
        "id_token": "fake_google_id_token_for_testing"
    }


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user profile data."""
    return {
        "user_id": "usr_test123",
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/avatar.jpg",
        "google_id": "google_123456"
    }


@pytest.fixture
def sample_enhancement_data() -> dict:
    """Sample enhancement data for database."""
    return {
        "enhancement_id": "enh_test123",
        "user_id": "usr_test123",
        "prompt_type": "photo",
        "prompt_title": None,
        "prompt_youtube_thumbnail_url": None,
        "source_photo_base64": "fake_base64_image_data",
        "source_transcript": None,
        "user_transcript": "Original story text",
        "enhanced_transcript": "Enhanced story text with improvements",
        "insights": {"plot": "Good story structure", "character": "Strong protagonist"},
        "audio_status": "not_generated",
        "audio_duration_seconds": None,
        "language": "en"
    }


# Legacy fixtures for backward compatibility
@pytest.fixture
def sample_story_text() -> str:
    """Sample story text for testing."""
    return """
    Once upon a time, in a small village nestled between rolling hills,
    there lived a young baker named Emma. Every morning, she would wake
    before dawn to prepare fresh bread for the villagers.
    """


@pytest.fixture
def sample_login_request() -> dict:
    """Sample login request data (legacy)."""
    return {
        "username": "demo",
        "password": "demo"
    }
