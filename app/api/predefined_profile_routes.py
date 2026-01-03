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