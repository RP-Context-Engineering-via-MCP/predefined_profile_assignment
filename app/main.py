# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.db_init import init_db
from app.api.predefined_profile_routes import router as predefined_profile_router
from app.api.user_routes import router as user_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Predefined Profile Assignment Service",
        version="1.0.0"
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
        allow_origins=["*"],          # ⚠️ Only for development!
        allow_credentials=False,      # Must be False when using "*"
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(predefined_profile_router)
    app.include_router(user_router)

    return app


app = create_app()


@app.on_event("startup")
def on_startup():
    """
    Initialize database schema on first startup.
    Safe to run multiple times.
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