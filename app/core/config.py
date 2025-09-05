"""
Configuration settings for the Amplify Backend application.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    api_title: str = "Amplify Backend API"
    api_version: str = "1.0.0"
    api_description: str = "Backend service for the Amplify application"
    
    # Server Configuration
    server_host: str = "0.0.0.0"
    server_port: int = 5000
    debug: bool = True
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # External APIs
    gemini_api_key: Optional[str] = None
    tts_api_key: Optional[str] = None
    
    # Database
    database_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()