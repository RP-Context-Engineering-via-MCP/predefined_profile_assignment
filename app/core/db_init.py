"""Database Initialization and Seeding Module.

This module handles database schema creation and initial data seeding.
Ensures all ORM models are registered with SQLAlchemy and executes
seed SQL scripts for predefined profiles and reference data.

All operations are idempotent and safe to run multiple times.
"""

from sqlalchemy import text
from app.core.database import engine, Base

from app.models import (
    profile,
    intent,
    profile_intent,
    interest_area,
    profile_interest,
    behavior_level,
    profile_behavior_level,
    behavior_signal,
    profile_behavior_signal,
    standard_matching_factor,
    cold_start_matching_factor,
    user,
    user_profile_ranking_state,
    output_preference,
    interaction_tone,
    domain_expertise_level,
    profile_output_preference,
    profile_tone,
    user_domain_state,
)

SEED_SQL_PATH = "app/core/initial_seed.sql"


def run_migrations() -> None:
    """Run schema migrations to add new columns.
    
    Adds new AI context columns to the profile table if they don't exist.
    Uses idempotent ALTER TABLE ADD COLUMN IF NOT EXISTS statements.
    """
    migration_sql = """
    -- Add new AI context columns to profile table if they don't exist
    ALTER TABLE profile ADD COLUMN IF NOT EXISTS context_statement TEXT;
    ALTER TABLE profile ADD COLUMN IF NOT EXISTS assumptions TEXT;
    ALTER TABLE profile ADD COLUMN IF NOT EXISTS ai_guidance TEXT;
    ALTER TABLE profile ADD COLUMN IF NOT EXISTS preferred_response_style TEXT;
    ALTER TABLE profile ADD COLUMN IF NOT EXISTS context_injection_prompt TEXT;
    """
    
    with engine.begin() as conn:
        conn.execute(text(migration_sql))


def seed_data() -> None:
    """Seed initial reference data from SQL script.
    
    Executes SQL statements from initial_seed.sql to populate predefined
    profiles, intents, domains, interests, behaviors, traits, and matching
    factors. Uses idempotent INSERT ON CONFLICT statements.
    
    Raises:
        Exception: If SQL file cannot be read or execution fails.
    """
    with open(SEED_SQL_PATH, "r", encoding="utf-8") as f:
        seed_sql = f.read()

    with engine.begin() as conn:
        conn.execute(text(seed_sql))


def init_db() -> None:
    """Initialize complete database schema and seed data.
    
    Performs three-step initialization:
    1. Creates all tables from ORM model metadata
    2. Runs schema migrations to add new columns
    3. Seeds initial reference data from SQL script
    
    Safe to run multiple times - all operations are idempotent.
    Call during application startup to ensure database readiness.
    
    Raises:
        Exception: If schema creation or seeding fails.
    """
    Base.metadata.create_all(bind=engine)
    run_migrations()
    seed_data()