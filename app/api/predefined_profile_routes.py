"""Predefined Profile Assignment API Routes Module.

This module provides RESTful API endpoints for profile assignment operations:
- Retrieving user profile assignment status with aggregated rankings
- Assigning profiles based on extracted behavior data
- Supporting both COLD_START and DRIFT_FALLBACK user modes

Profile assignment uses behavioral signals to match users with predefined
profiles based on complexity, consistency, and behavioral compatibility.
Also updates user domain expertise state based on behavior signals.
"""

from fastapi import APIRouter, Depends, HTTPException, Path
from app.services.profile_assigner import ProfileAssigner
from app.services.domain_expertise_service import DomainExpertiseService
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
    User mode is automatically retrieved from the user's database record.
    Supports two modes:
    - COLD_START: Single behavior dict for new users (initial assignment)
    - DRIFT_FALLBACK: List of behavior dicts for multi-prompt processing
    
    Updates ranking state with new observations and recalculates profile assignments
    based on complexity, consistency, and behavioral matching.
    
    Also updates user domain expertise state for each interest in the behavior data.
    
    Args:
        payload: BehaviorInputDTO containing:
            - user_id: Unique user identifier
            - behavior: Single dict (COLD_START) or list of dicts (DRIFT_FALLBACK)
        db: Database session dependency.
        
    Returns:
        dict: Assignment result containing:
            - assigned_profile_id: Selected profile
            - confidence: Assignment confidence (0.0-1.0)
            - aggregated_rankings: Scores for all profiles
            - match_details: Detailed matching factors
            - expertise_updates: Domain expertise update results
        
    Raises:
        HTTPException 400: If user_id missing or behavior format invalid for mode.
        HTTPException 404: If user not found in database.
        HTTPException 500: If profile assignment process fails.
    """
    if not payload.user_id:
        raise HTTPException(
            status_code=400, 
            detail="user_id is required for profile assignment"
        )
    
    assigner = ProfileAssigner(db)
    expertise_service = DomainExpertiseService(db)
    behavior = payload.behavior

    try:
        # Assign profile
        result = assigner.assign(
            extracted_behavior=behavior,
            user_id=payload.user_id
        )
        
        # Update domain expertise based on behavior data
        expertise_updates = None
        try:
            if isinstance(behavior, dict):
                # Single behavior dict (COLD_START)
                expertise_updates = expertise_service.update_expertise_from_json(
                    user_id=payload.user_id,
                    behavior_data=behavior
                )
            elif isinstance(behavior, list):
                # List of behavior dicts (DRIFT_FALLBACK)
                expertise_updates = expertise_service.update_expertise_from_json_batch(
                    user_id=payload.user_id,
                    behavior_batch=behavior
                )
        except Exception as exp_error:
            # Don't fail the whole request if expertise update fails
            # Just log and continue
            expertise_updates = {
                "error": str(exp_error),
                "status": "failed"
            }
        
        # Add expertise updates to result
        result["expertise_updates"] = expertise_updates
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))