# Core package initialization
"""Core application components.

This module provides the central orchestration and configuration
for the Predefined Profile Service.
"""

from app.core.config import settings
from app.core.intake_orchestrator import IntakeOrchestrator

__all__ = ["settings", "IntakeOrchestrator"]
