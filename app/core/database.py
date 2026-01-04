"""Database Connection and Session Management Module.

This module provides SQLAlchemy database engine, session factory, and dependency
injection for database sessions throughout the application. Uses connection
parameters from application settings.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


def get_db() -> Session:
    """Database session dependency for FastAPI.
    
    Provides database session to request handlers via dependency injection.
    Ensures proper session lifecycle with automatic cleanup.
    
    Yields:
        Session: SQLAlchemy database session.
        
    Note:
        Session is automatically closed after request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
