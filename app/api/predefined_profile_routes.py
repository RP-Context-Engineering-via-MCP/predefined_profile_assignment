# app/api/predefined_profile_routes.py

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
    """
    Get current profile assignment status and aggregated rankings for a user.
    
    Args:
        user_id: User ID to retrieve status for
        db: Database session dependency
        
    Returns:
        Current profile assignment status with confidence levels and aggregated rankings
    """
    assigner = ProfileAssigner(db)
    
    try:
        result = assigner.get_assignment_status(user_id=user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assign-profile")
def assign_profile(payload: BehaviorInputDTO, db=Depends(get_db)):
    """
    Assign a profile based on extracted behavior and update ranking state.
    
    For COLD_START mode: Pass a single behavior dict
    For DRIFT_FALLBACK mode: Pass a list of behavior dicts to process multiple prompts at once
    
    Args:
        payload: BehaviorInputDTO containing behavior data, user_id, and user_mode
        db: Database session dependency
        
    Returns:
        Profile assignment result with confidence levels and aggregated rankings
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