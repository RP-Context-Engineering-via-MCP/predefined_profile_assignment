# app/core/db_init.py

from sqlalchemy import text
from app.core.database import engine, Base

# IMPORTANT: import all models so SQLAlchemy registers them
from app.models import (
    profile,
    intent,
    profile_intent,
    domain,
    profile_domain,
    interest_area,
    profile_interest,
    behavior_level,
    profile_behavior_level,
    behavior_signal,
    profile_behavior_signal,
    trait,
    profile_trait,
    matching_factor,
    profile_version,
    user,
    user_profile_ranking_state,
)

SEED_SQL_PATH = "app/core/initial_seed.sql"


def seed_data() -> None:
    """Seed initial data using raw SQL (idempotent)."""
    with open(SEED_SQL_PATH, "r", encoding="utf-8") as f:
        seed_sql = f.read()

    with engine.begin() as conn:
        conn.execute(text(seed_sql))


def init_db() -> None:
    """
    Initialize database schema and seed initial data.
    Safe to run multiple times.
    """
    # 1. Create tables
    Base.metadata.create_all(bind=engine)

    # 2. Seed data
    seed_data()