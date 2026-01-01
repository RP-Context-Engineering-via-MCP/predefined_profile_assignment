# app/schemas/ranking_state_dto.py

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List


class RankingStateCreateRequest(BaseModel):
    """Schema for creating a new ranking state"""
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
    """Schema for updating a ranking state"""
    cumulative_score: Optional[float] = Field(None, ge=0.0)
    average_score: Optional[float] = Field(None, ge=0.0)
    max_score: Optional[float] = Field(None, ge=0.0)
    observation_count: Optional[int] = Field(None, ge=0)
    last_rank: Optional[int] = Field(None, ge=0)
    consecutive_top_count: Optional[int] = Field(None, ge=0)
    consecutive_drop_count: Optional[int] = Field(None, ge=0)


class ScoreUpdateRequest(BaseModel):
    """Schema for updating scores with a new observation"""
    new_score: float = Field(..., ge=0.0, description="New score to add")
    new_rank: int = Field(..., ge=1, description="New rank position")

    @validator('new_rank')
    def validate_rank(cls, v):
        if v < 1:
            raise ValueError('Rank must be at least 1')
        return v


class RankingStateResponse(BaseModel):
    """Schema for ranking state response"""
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
    """Schema for ranking state list response"""
    total: int
    states: List[RankingStateResponse]

    class Config:
        from_attributes = True


class RankingStatsSummary(BaseModel):
    """Summary statistics for a user's ranking states"""
    user_id: str
    total_profiles: int
    top_ranked_profile_id: Optional[str] = None
    highest_average_score: float
    total_observations: int
    profiles_with_drift: int


class ProfileRankingHistory(BaseModel):
    """Historical ranking information for a profile"""
    profile_id: str
    user_id: str
    current_rank: int
    average_score: float
    score_trend: str  # "improving", "stable", "declining"
    observation_count: int
    last_updated: datetime


class DriftDetectionResponse(BaseModel):
    """Response for drift detection analysis"""
    user_id: str
    profile_id: str
    has_drift: bool
    drift_type: Optional[str] = None  # "consistent_top", "consistent_drop", "volatile"
    consecutive_top_count: int
    consecutive_drop_count: int
    recommendation: str