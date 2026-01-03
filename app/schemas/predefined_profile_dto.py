# app/schemas/predefined_profile_dto.py

from pydantic import BaseModel, Field
from typing import Dict


class BehaviorInputDTO(BaseModel):
    """
    Input DTO for profile assignment
    """
    behavior: Dict = Field(..., description="Extracted behavior features (intents, interests, signals, behavior_level, consistency, complexity)")
    user_id: str = Field(..., description="User ID for ranking state persistence")
    user_mode: str = Field(default='COLD_START', description="User mode: 'COLD_START' or 'DRIFT_FALLBACK'")