#!/usr/bin/env python3
"""
Reinitialize database with updated seed data.
Run this after updating initial_seed.sql
"""

from app.core.db_init import init_db

if __name__ == "__main__":
    print("Reinitializing database with updated seed data...")
    try:
        init_db()
        print("✅ Database reinitialized successfully!")
        print("\nNew seed data includes:")
        print("  - LEARNING, EXPLORATION intents")
        print("  - AI, DATA_SCIENCE interests")
        print("  - ADVANCED behavior level")
        print("  - DEEP_REASONING, MULTI_STEP signals")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
