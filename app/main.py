"""FastAPI Application Entry Point.

This module creates and configures the FastAPI application instance,
including middleware setup, router registration, and application lifecycle
event handlers for database initialization.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.db_init import init_db
from app.core.logging_config import setup_logging
from app.api.predefined_profile_routes import router as predefined_profile_router
from app.api.user_routes import router as user_router
from app.api.ranking_state_routes import router as ranking_state_router
from app.api.domain_expertise_routes import router as domain_expertise_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application instance.
    
    Sets up:
    - Logging configuration
    - FastAPI app with metadata
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
        description="AI-powered user profile assignment and matching service"
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


@app.on_event("startup")
def on_startup():
    """Initialize database schema and seed data on application startup.
    
    Executes database initialization including table creation and reference
    data seeding. Safe to run multiple times due to idempotent operations.
    """
    init_db()


@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Predefined Profile Assignment Service",
        "version": "1.0.0"
    }