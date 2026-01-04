# app/core/config.py

from pydantic import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Supabase PostgreSQL connection
    DATABASE_URL: str

    # Application settings
    APP_NAME: str = "Predefined Profile Assignment Service"
    ENVIRONMENT: str = "development"
    
    # OAuth Configuration
    JWT_SECRET_KEY: str = "your-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # GitHub OAuth
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
