"""
Configuration settings for the Amplify Backend application.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
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

    # AI Provider Configuration
    ai_provider: str = "gemini"  # "gemini" or "openai"
    gemini_model: str = "models/gemini-2.5-flash-lite"
    openai_model: str = "gpt-4-vision-preview"

    # TTS Configuration
    tts_provider: str = "openai"  # "openai", "elevenlabs", or "mock"
    tts_voice: str = "alloy"  # OpenAI: alloy, echo, fable, onyx, nova, shimmer

    # Database
    database_url: Optional[str] = None

    # Prompt Management
    prompts_path: str = "app/prompts"
    prompts_hot_reload: bool = True  # Auto-set based on debug mode in production

    @validator('ai_provider')
    def validate_ai_provider(cls, v):
        """Validate AI provider setting."""
        valid_providers = ["gemini", "openai"]
        if v not in valid_providers:
            raise ValueError(f"Invalid AI provider: {v}. Must be one of {valid_providers}")
        return v

    @validator('openai_model')
    def validate_openai_model(cls, v):
        """Validate OpenAI model setting."""
        valid_models = [
            "gpt-4-vision-preview",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo"
        ]
        if v not in valid_models:
            raise ValueError(f"Invalid OpenAI model: {v}. Must be one of {valid_models}")
        return v

    @property
    def supports_vision(self) -> bool:
        """Check if the current AI provider and model support vision capabilities."""
        if self.ai_provider == "gemini":
            return True  # All Gemini models support vision
        elif self.ai_provider == "openai":
            vision_models = ["gpt-4-vision-preview", "gpt-4-turbo"]
            return self.openai_model in vision_models
        return False

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
