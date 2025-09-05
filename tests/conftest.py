"""
Global pytest fixtures for all tests.
"""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import asyncio
from typing import Generator

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncClient:
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as async_test_client:
        yield async_test_client


@pytest.fixture
def sample_story_text() -> str:
    """Sample story text for testing."""
    return """
    Once upon a time, in a small village nestled between rolling hills, 
    there lived a young baker named Emma. Every morning, she would wake 
    before dawn to prepare fresh bread for the villagers.
    """


@pytest.fixture
def sample_enhancement_request() -> dict:
    """Sample enhancement request data."""
    return {
        "story_text": "Once upon a time, there was a brave knight.",
        "enhancement_type": "plot"
    }


@pytest.fixture
def sample_audio_request() -> dict:
    """Sample audio generation request data."""
    return {
        "text": "Hello, this is a test message.",
        "voice_id": "voice-1",
        "speed": 1.0
    }


@pytest.fixture
def sample_login_request() -> dict:
    """Sample login request data."""
    return {
        "username": "demo",
        "password": "demo"
    }