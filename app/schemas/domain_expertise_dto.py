"""Domain Expertise DTOs.

Pydantic schemas for user domain expertise tracking.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class DomainExpertiseStateResponse(BaseModel):
    """Response schema for user domain expertise state."""
    
    user_id: str = Field(..., description="User identifier")
    interest_id: int = Field(..., description="Interest domain identifier")
    expertise_level_id: int = Field(..., description="Expertise level ID")
    expertise_level: str = Field(..., description="Expertise level name (BEGINNER/INTERMEDIATE/ADVANCED)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)")
    last_updated: datetime = Field(..., description="Last update timestamp")

    class Config:
        orm_mode = True


class DomainExpertiseUpdateRequest(BaseModel):
    """Request schema for updating domain expertise."""
    
    user_id: str = Field(..., description="User identifier")
    interest_id: int = Field(..., description="Interest domain identifier")
    prompt: str = Field(..., min_length=1, description="User prompt to analyze")
    complexity_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Optional complexity score")


class DomainExpertiseUpdateResponse(BaseModel):
    """Response schema for expertise update operation."""
    
    user_id: str = Field(..., description="User identifier")
    interest_id: int = Field(..., description="Interest domain identifier")
    old_confidence: float = Field(..., description="Previous confidence score")
    new_confidence: float = Field(..., description="New confidence score")
    confidence_delta: float = Field(..., description="Change in confidence")
    signals_detected: list = Field(..., description="List of detected signal names")
    signal_values: dict = Field(..., description="Signal names and their delta values")
    expertise_level: str = Field(..., description="Current expertise level")
    level_changed: bool = Field(..., description="Whether expertise level changed")


class DomainExpertiseInitRequest(BaseModel):
    """Request schema for cold-start initialization."""
    
    user_id: str = Field(..., description="User identifier")
    interest_id: int = Field(..., description="Interest domain identifier")


class DomainExpertiseInitResponse(BaseModel):
    """Response schema for cold-start initialization."""
    
    user_id: str = Field(..., description="User identifier")
    interest_id: int = Field(..., description="Interest domain identifier")
    expertise_level: str = Field(default="BEGINNER", description="Initial expertise level")
    confidence_score: float = Field(..., description="Initial confidence score")
    initialized: bool = Field(default=True, description="Initialization success flag")


class UserDomainStatesResponse(BaseModel):
    """Response schema for all user domain states."""
    
    user_id: str = Field(..., description="User identifier")
    domain_states: list = Field(..., description="List of domain expertise states")
    total_domains: int = Field(..., description="Total number of tracked domains")


class ExpertiseDecayRequest(BaseModel):
    """Request schema for applying expertise decay."""
    
    days_threshold: int = Field(default=30, ge=1, description="Days of inactivity before decay")
    decay_factor: float = Field(default=0.98, ge=0.0, le=1.0, description="Decay multiplier")


class ExpertiseDecayResponse(BaseModel):
    """Response schema for decay operation."""
    
    records_updated: int = Field(..., description="Number of records updated")
    success: bool = Field(default=True, description="Operation success flag")
