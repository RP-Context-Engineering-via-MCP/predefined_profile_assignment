"""Predefined profile data transfer objects.

Provides schemas for profile assignment requests based on user behavior data.
Supports both cold-start scenarios and drift-fallback mechanisms.
"""

from pydantic import BaseModel, Field
from typing import Dict, Union, List, Optional


class BehaviorInputDTO(BaseModel):
    """Behavior input schema for profile assignment (legacy sync endpoint).
    
    Accepts behavioral data in different formats depending on user mode.
    Used by profile matcher to determine best-fitting predefined profile.
    User mode is automatically retrieved from the user's database record.
    
    Attributes:
        behavior: Single behavior dict (COLD_START) or list of dicts (DRIFT_FALLBACK).
                 Each dict must contain: intents, interests, signals, behavior_level,
                 consistency, and complexity scores.
        user_id: User identifier for persisting ranking state and retrieving user mode
    """
    behavior: Union[Dict, List[Dict]] = Field(..., description="Single behavior dict for COLD_START or list of behavior dicts for DRIFT_FALLBACK. Each dict contains: (intents, interests, signals, behavior_level, consistency, complexity)")
    user_id: str = Field(..., description="User ID for ranking state persistence and mode retrieval")


class AssignProfileRequest(BaseModel):
    """Profile assignment request schema for async endpoint.
    
    Used by Behavior Resolution Mechanism (cold start) and Drift Detection
    Service (drift fallback) to request profile assignment.
    
    Attributes:
        user_id: UUID of the target user
        mode: Assignment mode - "COLD_START" or "DRIFT_FALLBACK"
        extracted_behavior: Behavior signals from Behavior Resolution.
            - COLD_START: Single dict with intents, interests, signals, behavior_level,
              consistency, complexity
            - DRIFT_FALLBACK: List of such dicts (recent prompts)
        trigger_event_id: Drift event ID if mode is DRIFT_FALLBACK (optional)
    """
    user_id: str = Field(..., description="UUID of the target user")
    mode: str = Field(
        default="COLD_START",
        description="Assignment mode: COLD_START or DRIFT_FALLBACK"
    )
    extracted_behavior: Union[Dict, List[Dict]] = Field(
        ..., 
        description="Behavior signals dict (COLD_START) or list of dicts (DRIFT_FALLBACK)"
    )
    trigger_event_id: Optional[str] = Field(
        default=None,
        description="Drift event ID if triggered by drift detection"
    )


class AssignmentStatusResponse(BaseModel):
    """Profile assignment status response schema.
    
    Attributes:
        status: Assignment status - "ASSIGNED", "PENDING", or "NOT_FOUND"
        confidence_level: Confidence in assignment - "HIGH", "MEDIUM", "LOW", "NONE"
        user_mode: Current profile mode of the user
        prompt_count: Number of prompts processed
        assigned_profile_id: Currently assigned profile ID or None
        aggregated_rankings: List of profile ranking states
    """
    status: str
    confidence_level: str
    user_mode: str
    prompt_count: int
    assigned_profile_id: Optional[str] = None
    aggregated_rankings: List[Dict] = []


# =============================================================================
# Profile Context DTOs - Full profile attributes for downstream services
# =============================================================================

class WeightedItemDTO(BaseModel):
    """Generic weighted item for profile attributes.
    
    Attributes:
        name: Item name (e.g., intent name, interest name)
        weight: Relative importance (0.0 to 1.0)
        description: Optional description of the item
    """
    name: str
    weight: float
    description: Optional[str] = None


class IntentDTO(WeightedItemDTO):
    """Profile intent with primary flag.
    
    Attributes:
        name: Intent name (e.g., 'LEARNING', 'TASK_COMPLETION')
        weight: Relative importance (0.0 to 1.0)
        is_primary: Whether this is the primary intent for the profile
        description: Intent description
    """
    is_primary: bool = False


class ProfileContextResponse(BaseModel):
    """Profile context for downstream services (LLM Orchestration).
    
    Contains AI guidance context for LLM personalization.
    Used by LLM Orchestration and other services to personalize responses.
    
    Attributes:
        profile_id: Unique profile identifier (P1-P6)
        profile_name: Human-readable profile name
        context_statement: Brief context about what user wants (e.g., "This user wants to understand")
        assumptions: List of assumptions about the user
        ai_guidance: List of guidance instructions for AI behavior
        preferred_response_style: List of style labels (e.g., ["Educational", "Structured"])
        context_injection_prompt: Ready-to-use prompt for AI context injection
    """
    profile_id: str
    profile_name: str
    context_statement: Optional[str] = None
    assumptions: List[str] = []
    ai_guidance: List[str] = []
    preferred_response_style: List[str] = []
    context_injection_prompt: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProfileListResponse(BaseModel):
    """List of all profiles with basic info.
    
    Attributes:
        profiles: List of profile summaries
        total: Total number of profiles
    """
    profiles: List[ProfileContextResponse]
    total: int