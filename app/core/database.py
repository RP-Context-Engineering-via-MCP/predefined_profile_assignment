"""Database Connection and Session Management Module.

This module provides SQLAlchemy database engine, session factory, and dependency
injection for database sessions throughout the application. Uses connection
parameters from application settings.

Supports both synchronous and asynchronous database operations:
- Synchronous: Used by existing repositories and services
- Asynchronous: Used by Redis consumers and publishers
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings


# =============================================================================
# Synchronous Database (existing - used by repositories)
# =============================================================================

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


def get_db() -> Session:
    """Database session dependency for FastAPI (synchronous).
    
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


# =============================================================================
# Asynchronous Database (new - used by consumers/publishers)
# =============================================================================

def _get_async_database_url() -> str:
    """Convert sync database URL to async format.
    
    Converts postgresql+psycopg:// to postgresql+psycopg_async://
    psycopg3 requires the _async suffix for async connections.
    """
    url = settings.DATABASE_URL
    # psycopg (v3) needs _async suffix for async operations
    if "+psycopg:" in url or "+psycopg/" in url:
        return url.replace("+psycopg", "+psycopg_async", 1)
    # For plain postgresql://, use asyncpg
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


async_engine = create_async_engine(
    _get_async_database_url(),
    echo=settings.DEBUG,
    pool_size=10,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_db():
    """Async database session dependency for FastAPI.
    
    Provides async database session for async route handlers.
    
    Yields:
        AsyncSession: SQLAlchemy async database session.
    """
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Initialize database connection on application startup.
    
    Verifies database connectivity by executing a simple query.
    Should be called during FastAPI lifespan startup.
    
    Raises:
        Exception: If database connection fails.
    """
    async with async_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def close_db():
    """Close database connections on application shutdown.
    
    Disposes of the async engine connection pool.
    Should be called during FastAPI lifespan shutdown.
    """
    await async_engine.dispose()
