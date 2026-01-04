"""Application Configuration Module.

This module defines application-wide configuration settings using Pydantic BaseSettings.
Settings are loaded from environment variables or .env file and include:
- Database connection configuration
- JWT authentication settings  
- OAuth provider credentials
- Profile assignment algorithm parameters

All sensitive values should be provided via environment variables in production.
"""

from pydantic import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings.
    
    Loads configuration from environment variables or .env file.
    Provides type validation and default values for application settings.
    """
    DATABASE_URL: str

    APP_NAME: str = "Predefined Profile Assignment Service"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    JWT_SECRET_KEY: str = "your-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    
    MIN_PROMPTS_COLD_START: int = 3
    MIN_PROMPTS_FALLBACK: int = 5
    COLD_START_THRESHOLD: float = 0.60
    FALLBACK_THRESHOLD: float = 0.70
    HIGH_CONFIDENCE_THRESHOLD: float = 0.70

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
