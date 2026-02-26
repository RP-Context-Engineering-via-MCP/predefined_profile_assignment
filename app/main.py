"""FastAPI Application Entry Point.

This module creates and configures the FastAPI application instance,
including middleware setup, router registration, and application lifecycle
event handlers for database initialization.

The application runs two concurrent processes:
1. HTTP server - serves the REST API
2. Redis consumer loop - runs as background asyncio task, listening to drift.events
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.db_init import init_db
from app.core.logging_config import setup_logging
from app.core.database import init_db as init_async_db, close_db
from app.core.config import settings
from app.consumer.redis_consumer import DriftEventConsumer
from app.api.predefined_profile_routes import router as predefined_profile_router
from app.api.user_routes import router as user_router
from app.api.ranking_state_routes import router as ranking_state_router
from app.api.domain_expertise_routes import router as domain_expertise_router

logger = logging.getLogger(__name__)

# Global consumer instance for lifecycle management
_consumer_instance: Optional[DriftEventConsumer] = None
_consumer_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager.
    
    Handles startup and shutdown events:
    
    Startup:
    1. Initialize sync database schema (tables, seed data)
    2. Verify async database connection
    3. Start Redis drift event consumer as background task
    
    Shutdown:
    1. Stop Redis consumer gracefully
    2. Cancel consumer task
    3. Close async database connections
    """
    global _consumer_instance, _consumer_task
    
    # === STARTUP ===
    logger.info("Starting Predefined Profile Service...")
    
    # Initialize sync database schema and seed data
    init_db()
    logger.info("Database schema initialized")
    
    # Verify async database connection
    try:
        await init_async_db()
        logger.info("Async database connection verified")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise
    
    # Start Redis drift event consumer as background task
    try:
        _consumer_instance = DriftEventConsumer()
        _consumer_task = asyncio.create_task(_consumer_instance.start())
        logger.info("Drift event consumer started")
    except Exception as e:
        logger.warning(f"Failed to start drift event consumer: {e}")
        # Don't fail startup - service can still handle HTTP requests
    
    logger.info("Predefined Profile Service started successfully")
    
    yield  # Service is running
    
    # === SHUTDOWN ===
    logger.info("Shutting down Predefined Profile Service...")
    
    # Stop Redis consumer gracefully
    if _consumer_instance is not None:
        _consumer_instance.stop()
        await _consumer_instance.close()
        logger.info("Drift event consumer stopped")
    
    # Cancel consumer task
    if _consumer_task is not None:
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass
        logger.info("Consumer task cancelled")
    
    # Close async database connections
    await close_db()
    logger.info("Database connections closed")
    
    logger.info("Predefined Profile Service shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application instance.
    
    Sets up:
    - Logging configuration
    - FastAPI app with metadata and lifespan manager
    - CORS middleware for cross-origin requests
    - API route registration
    
    Returns:
        FastAPI: Configured application instance ready to serve requests.
    """
    # Initialize logging
    setup_logging()
    
    app = FastAPI(
        title="Predefined Profile Assignment Service",
        version="1.0.0",
        description="AI-powered user profile assignment and matching service",
        lifespan=lifespan
    )

    # Configure CORS
    origins = [
        "http://localhost:5173",      # Vite default port
        "http://localhost:3000",      # React default port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost:5174",      # Alternative Vite port
        "http://127.0.0.1:5174",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(predefined_profile_router)
    app.include_router(user_router)
    app.include_router(ranking_state_router)
    app.include_router(domain_expertise_router)

    return app


app = create_app()


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Predefined Profile Assignment Service",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint.
    
    Returns service health status including component states.
    """
    consumer_status = "running" if (_consumer_instance and _consumer_instance._running) else "stopped"
    
    return {
        "status": "healthy",
        "service": "Predefined Profile Assignment Service",
        "version": "1.0.0",
        "components": {
            "http_server": "running",
            "drift_consumer": consumer_status,
            "database": "connected"
        }
    }