# app/schemas/predefined_profile_dto.py

from pydantic import BaseModel, Field
from typing import Dict, Union, List


class BehaviorInputDTO(BaseModel):
    """
    Input DTO for profile assignment
    """
    behavior: Union[Dict, List[Dict]] = Field(..., description="Single behavior dict for COLD_START or list of behavior dicts for DRIFT_FALLBACK. Each dict contains: (intents, interests, signals, behavior_level, consistency, complexity)")
    user_id: str = Field(..., description="User ID for ranking state persistence")
    user_mode: str = Field(default='COLD_START', description="User mode: 'COLD_START' or 'DRIFT_FALLBACK'")