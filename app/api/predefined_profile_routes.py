"""Predefined Profile Assignment API Routes Module.

This module provides RESTful API endpoints for profile assignment operations:
- Retrieving user profile assignment status with aggregated rankings
- Assigning profiles based on extracted behavior data
- Supporting both COLD_START and DRIFT_FALLBACK user modes

Profile assignment uses behavioral signals to match users with predefined
profiles based on complexity, consistency, and behavioral compatibility.
"""

from fastapi import APIRouter, Depends, HTTPException, Path
from app.services.profile_assigner import ProfileAssigner
from app.schemas.predefined_profile_dto import BehaviorInputDTO
from app.core.database import get_db

router = APIRouter(
    prefix="/api/predefined-profiles",
    tags=["profile-assignment"]
)


@router.get("/user/{user_id}")
def get_profile_assignment_status(
    user_id: str = Path(..., description="User ID to retrieve profile assignment status"),
    db=Depends(get_db)
):
    """Retrieve current profile assignment status for user.
    
    Provides comprehensive profile assignment information including assigned profile,
    confidence levels, and aggregated rankings across all predefined profiles.
    
    Args:
        user_id: Unique user identifier.
        db: Database session dependency.
        
    Returns:
        dict: Profile assignment status containing:
            - assigned_profile_id: Currently assigned profile
            - confidence: Assignment confidence level
            - aggregated_rankings: Scores for all profiles
            - ranking_states: Individual ranking state details
        
    Raises:
        HTTPException 500: If status retrieval fails.
    """
    assigner = ProfileAssigner(db)
    
    try:
        result = assigner.get_assignment_status(user_id=user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assign-profile")
def assign_profile(payload: BehaviorInputDTO, db=Depends(get_db)):
    """Assign predefined profile based on extracted behavior data.
    
    Processes user behavior to assign the most suitable predefined profile.
    Supports two modes:
    - COLD_START: Single behavior dict for new users (initial assignment)
    - DRIFT_FALLBACK: List of behavior dicts for multi-prompt processing
    
    Updates ranking state with new observations and recalculates profile assignments
    based on complexity, consistency, and behavioral matching.
    
    Args:
        payload: BehaviorInputDTO containing:
            - user_id: Unique user identifier
            - user_mode: Assignment mode (COLD_START or DRIFT_FALLBACK)
            - behavior: Single dict (COLD_START) or list of dicts (DRIFT_FALLBACK)
        db: Database session dependency.
        
    Returns:
        dict: Assignment result containing:
            - assigned_profile_id: Selected profile
            - confidence: Assignment confidence (0.0-1.0)
            - aggregated_rankings: Scores for all profiles
            - match_details: Detailed matching factors
        
    Raises:
        HTTPException 400: If user_id missing or behavior format invalid for mode.
        HTTPException 500: If profile assignment process fails.
    """
    if not payload.user_id:
        raise HTTPException(
            status_code=400, 
            detail="user_id is required for profile assignment"
        )
    
    # Validate behavior based on user_mode
    if payload.user_mode == 'DRIFT_FALLBACK':
        if isinstance(payload.behavior, dict):
            raise HTTPException(
                status_code=400,
                detail="DRIFT_FALLBACK mode expects a list of behavior dicts, not a single dict"
            )
        if not isinstance(payload.behavior, list) or len(payload.behavior) == 0:
            raise HTTPException(
                status_code=400,
                detail="DRIFT_FALLBACK mode requires at least one behavior dict in the list"
            )
    elif payload.user_mode == 'COLD_START':
        if isinstance(payload.behavior, list):
            raise HTTPException(
                status_code=400,
                detail="COLD_START mode expects a single behavior dict, not a list"
            )
    
    assigner = ProfileAssigner(db)
    behavior = payload.behavior

    try:
        result = assigner.assign(
            extracted_behavior=behavior,
            user_id=payload.user_id,
            user_mode=payload.user_mode
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))