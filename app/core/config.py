"""Application Configuration Module.

This module defines application-wide configuration settings using Pydantic BaseSettings.
Settings are loaded from environment variables or .env file and include:
- Database connection configuration
- JWT authentication settings  
- OAuth provider credentials
- Profile assignment algorithm parameters
- Redis connection settings
- External service URLs

All sensitive values should be provided via environment variables in production.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings.
    
    Loads configuration from environment variables or .env file.
    Provides type validation and default values for application settings.
    """
    # Database
    DATABASE_URL: str

    # Application
    APP_NAME: str = "Predefined Profile Assignment Service"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # JWT Authentication
    JWT_SECRET_KEY: str = "your-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OAuth Providers
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    
    # External Services
    BEHAVIOR_RESOLUTION_BASE_URL: str = "http://localhost:8001"
    DRIFT_FALLBACK_BEHAVIOR_LIMIT: int = 10
    
    # Profile Assignment Thresholds
    MIN_PROMPTS_COLD_START: int = 3
    MIN_PROMPTS_FALLBACK: int = 5
    COLD_START_THRESHOLD: float = 0.60
    COLD_START_CONSECUTIVE_TOP: int = 2
    FALLBACK_THRESHOLD: float = 0.70
    FALLBACK_CONSECUTIVE_TOP: int = 3
    HIGH_CONFIDENCE_THRESHOLD: float = 0.70

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
