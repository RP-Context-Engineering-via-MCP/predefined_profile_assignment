# app/core/config.py

from pydantic import BaseSettings


class Settings(BaseSettings):
    # Supabase PostgreSQL connection
    DATABASE_URL: str

    # Application settings
    APP_NAME: str = "Predefined Profile Assignment Service"
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
