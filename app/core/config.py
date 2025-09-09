"""
Configuration settings for the Amplify Backend application.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    api_title: str = "Amplify Backend API"
    api_version: str = "1.0.0"
    api_description: str = "Backend service for the Amplify application"
    
    # Server Configuration
    server_host: str = "0.0.0.0"
    server_port: int = 8000  # Use 8000 locally (5000 is often used by macOS AirPlay)
    debug: bool = True
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200  # 30 days (30 * 24 * 60)
    
    # External APIs
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    google_client_id: Optional[str] = None  # Reads from GOOGLE_CLIENT_ID env var
    
    # TTS Configuration
    tts_provider: str = "openai"  # "openai", "elevenlabs", or "mock"
    tts_voice: str = "alloy"  # OpenAI: alloy, echo, fable, onyx, nova, shimmer
    
    # Database
    database_url: Optional[str] = None
    
    # Prompt Management
    prompts_path: str = "app/prompts"
    prompts_hot_reload: bool = True  # Auto-set based on debug mode in production
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()