"""Ranking state data transfer objects.

Provides schemas for tracking and managing profile ranking states,
including drift detection and temporal score aggregation.
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List


class RankingStateCreateRequest(BaseModel):
    """Ranking state creation request schema.
    
    Initializes tracking state for a user-profile pair.
    
    Attributes:
        user_id: User unique identifier (UUID format)
        profile_id: Profile unique identifier
        cumulative_score: Sum of all matching scores
        average_score: Mean matching score across observations
        max_score: Highest observed matching score
        observation_count: Number of scoring events
        last_rank: Most recent rank position
        consecutive_top_count: Consecutive times ranked first
        consecutive_drop_count: Consecutive rank drops
    """
    user_id: str = Field(..., min_length=36, max_length=36)
    profile_id: str = Field(..., min_length=24, max_length=24)
    cumulative_score: float = Field(default=0.0, ge=0.0)
    average_score: float = Field(default=0.0, ge=0.0)
    max_score: float = Field(default=0.0, ge=0.0)
    observation_count: int = Field(default=0, ge=0)
    last_rank: int = Field(default=0, ge=0)
    consecutive_top_count: int = Field(default=0, ge=0)
    consecutive_drop_count: int = Field(default=0, ge=0)


class RankingStateUpdateRequest(BaseModel):
    """Ranking state update request schema.
    
    Allows partial updates to ranking state metrics.
    All fields are optional.
    
    Attributes:
        cumulative_score: Updated cumulative score
        average_score: Updated average score
        max_score: Updated maximum score
        observation_count: Updated observation count
        last_rank: Updated last rank position
        consecutive_top_count: Updated consecutive top count
        consecutive_drop_count: Updated consecutive drop count
    """
    cumulative_score: Optional[float] = Field(None, ge=0.0)
    average_score: Optional[float] = Field(None, ge=0.0)
    max_score: Optional[float] = Field(None, ge=0.0)
    observation_count: Optional[int] = Field(None, ge=0)
    last_rank: Optional[int] = Field(None, ge=0)
    consecutive_top_count: Optional[int] = Field(None, ge=0)
    consecutive_drop_count: Optional[int] = Field(None, ge=0)


class ScoreUpdateRequest(BaseModel):
    """Score update request schema.
    
    Records new observation for incremental state updates.
    
    Attributes:
        new_score: New matching score (non-negative)
        new_rank: New rank position (minimum 1)
    """
    new_score: float = Field(..., ge=0.0, description="New score to add")
    new_rank: int = Field(..., ge=1, description="New rank position")

    @validator('new_rank')
    def validate_rank(cls, v):
        """Ensure rank is positive."""
        if v < 1:
            raise ValueError('Rank must be at least 1')
        return v


class RankingStateResponse(BaseModel):
    """Ranking state response schema.
    
    Attributes:
        id: Unique ranking state identifier
        user_id: User unique identifier
        profile_id: Profile unique identifier
        cumulative_score: Total accumulated score
        average_score: Mean score across observations
        max_score: Highest recorded score
        observation_count: Number of scoring events
        last_rank: Most recent rank position
        consecutive_top_count: Consecutive first-place ranks
        consecutive_drop_count: Consecutive rank decreases
        updated_at: Last update timestamp
    """
    id: str
    user_id: str
    profile_id: str
    cumulative_score: float
    average_score: float
    max_score: float
    observation_count: int
    last_rank: int
    consecutive_top_count: int
    consecutive_drop_count: int
    updated_at: datetime

    class Config:
        from_attributes = True


class RankingStateListResponse(BaseModel):
    """Paginated ranking state list response schema.
    
    Attributes:
        total: Total number of ranking states
        states: List of ranking state objects
    """
    total: int
    states: List[RankingStateResponse]

    class Config:
        from_attributes = True


class RankingStatsSummary(BaseModel):
    """User ranking statistics summary schema.
    
    Aggregates key metrics across all user-profile ranking states.
    
    Attributes:
        user_id: User unique identifier
        total_profiles: Number of tracked profiles
        top_ranked_profile_id: Currently top-ranked profile
        highest_average_score: Best average score across profiles
        total_observations: Total scoring events
        profiles_with_drift: Number of profiles showing drift
    """
    user_id: str
    total_profiles: int
    top_ranked_profile_id: Optional[str] = None
    highest_average_score: float
    total_observations: int
    profiles_with_drift: int


class ProfileRankingHistory(BaseModel):
    """Profile ranking history schema.
    
    Provides temporal view of profile ranking evolution.
    
    Attributes:
        profile_id: Profile unique identifier
        user_id: User unique identifier
        current_rank: Current rank position
        average_score: Mean score across observations
        score_trend: Trend direction (improving, stable, declining)
        observation_count: Number of scoring events
        last_updated: Last update timestamp
    """
    profile_id: str
    user_id: str
    current_rank: int
    average_score: float
    score_trend: str
    observation_count: int
    last_updated: datetime


class DriftDetectionResponse(BaseModel):
    """Drift detection analysis response schema.
    
    Identifies behavioral drift patterns requiring intervention.
    
    Attributes:
        user_id: User unique identifier
        profile_id: Profile being analyzed
        has_drift: Flag indicating drift detection
        drift_type: Classification (consistent_top, consistent_drop, volatile)
        consecutive_top_count: Consecutive first-place ranks
        consecutive_drop_count: Consecutive rank decreases
        recommendation: Suggested action or explanation
    """
    user_id: str
    profile_id: str
    has_drift: bool
    drift_type: Optional[str] = None
    consecutive_top_count: int
    consecutive_drop_count: int
    recommendation: str