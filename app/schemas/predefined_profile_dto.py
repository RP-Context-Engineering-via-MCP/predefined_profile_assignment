# app/schemas/predefined_profile_dto.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, List


class SessionHistoryDTO(BaseModel):
    """Session history for consistency calculation"""
    intent_history: Optional[List[str]] = Field(default_factory=list)
    domain_history: Optional[List[str]] = Field(default_factory=list)
    signal_history: Optional[Dict[str, List[float]]] = None


class BehaviorInputDTO(BaseModel):
    """
    Input DTO for profile assignment
    
    UPDATED: Added user_mode and assignment threshold parameters
    """
    behavior: Dict = Field(..., description="Extracted behavior features")
    prompt_count: int = Field(..., ge=1, description="Number of prompts in session")
    user_id: str = Field(..., description="User ID for ranking state persistence")
    

    user_mode: str = Field(
        default='COLD_START',
        description="User mode: 'COLD_START' or 'DRIFT_FALLBACK'"
    )
    

    complexity: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0,
        description="Prompt complexity score (0-1)"
    )
    consistency: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Pre-computed consistency score"
    )
    session_history: Optional[SessionHistoryDTO] = Field(
        None,
        description="Session history for consistency calculation"
    )
    

    min_prompts_for_assignment: int = Field(
        default=3,
        ge=1,
        description="Minimum observations required before cold-start assignment"
    )
    cold_start_threshold: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Average score threshold for cold-start assignment"
    )
    fallback_threshold: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Average score threshold for fallback assignment"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "behavior": {
                    "intents": {"LEARN": 0.8, "EXPLORE": 0.5},
                    "interests": {"TECH": 0.7, "SCIENCE": 0.6},
                    "signals": {"CONCISE": 0.6, "VISUAL": 0.4},
                    "behavior_level": "INTERMEDIATE",
                    "complexity": 0.65,
                    "consistency": 0.7
                },
                "prompt_count": 4,
                "user_id": "user_123",
                "user_mode": "COLD_START",
                "min_prompts_for_assignment": 3,
                "cold_start_threshold": 0.60,
                "fallback_threshold": 0.70
            }
        }