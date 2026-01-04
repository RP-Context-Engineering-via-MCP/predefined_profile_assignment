"""Predefined profile data transfer objects.

Provides schemas for profile assignment requests based on user behavior data.
Supports both cold-start scenarios and drift-fallback mechanisms.
"""

from pydantic import BaseModel, Field
from typing import Dict, Union, List


class BehaviorInputDTO(BaseModel):
    """Behavior input schema for profile assignment.
    
    Accepts behavioral data in different formats depending on user mode.
    Used by profile matcher to determine best-fitting predefined profile.
    
    Attributes:
        behavior: Single behavior dict (COLD_START) or list of dicts (DRIFT_FALLBACK).
                 Each dict must contain: intents, interests, signals, behavior_level,
                 consistency, and complexity scores.
        user_id: User identifier for persisting ranking state
        user_mode: Assignment mode ('COLD_START' for initial, 'DRIFT_FALLBACK' for corrections)
    """
    behavior: Union[Dict, List[Dict]] = Field(..., description="Single behavior dict for COLD_START or list of behavior dicts for DRIFT_FALLBACK. Each dict contains: (intents, interests, signals, behavior_level, consistency, complexity)")
    user_id: str = Field(..., description="User ID for ranking state persistence")
    user_mode: str = Field(default='COLD_START', description="User mode: 'COLD_START' or 'DRIFT_FALLBACK'")