# app/api/predefined_profile_routes.py

from fastapi import APIRouter, Depends, HTTPException
from app.services.profile_assigner import ProfileAssigner
from app.schemas.predefined_profile_dto import BehaviorInputDTO
from app.core.database import get_db

router = APIRouter()


@router.post("/assign-profile")
def assign_profile(payload: BehaviorInputDTO, db=Depends(get_db)):
    """
    Assign a profile based on extracted behavior and update ranking state.
    
    CORRECTED: Now accepts user_mode parameter and uses accumulated ranking state
    for assignment decisions.
    
    Args:
        payload: BehaviorInputDTO containing behavior data, user_id, and user_mode
        db: Database session dependency
        
    Returns:
        Profile assignment result with confidence levels
    """
    # Validate that user_id is provided
    if not payload.user_id:
        raise HTTPException(
            status_code=400, 
            detail="user_id is required for profile assignment"
        )
    
    assigner = ProfileAssigner(db)

    # If complexity is provided at root level, inject into behavior dict
    behavior = payload.behavior.copy()
    if payload.complexity is not None:
        behavior["complexity"] = payload.complexity
    
    # If complexity not in behavior, use default
    if "complexity" not in behavior:
        behavior["complexity"] = 0.5
    
    # Ensure consistency field exists in behavior
    if "consistency" not in behavior:
        behavior["consistency"] = 0.5
    
    # Ensure all required fields exist with defaults
    if "intents" not in behavior:
        behavior["intents"] = {}
    if "interests" not in behavior:
        behavior["interests"] = {}
    if "signals" not in behavior:
        behavior["signals"] = {}
    if "behavior_level" not in behavior:
        behavior["behavior_level"] = "INTERMEDIATE"

    # ✅ NEW: Get user_mode from payload (default to COLD_START)
    user_mode = getattr(payload, 'user_mode', 'COLD_START')
    
    # ✅ NEW: Optional assignment thresholds from payload
    min_prompts = getattr(payload, 'min_prompts_for_assignment', 3)
    cold_threshold = getattr(payload, 'cold_start_threshold', 0.60)
    fallback_threshold = getattr(payload, 'fallback_threshold', 0.70)

    try:
        result = assigner.assign(
            extracted_behavior=behavior,
            prompt_count=payload.prompt_count,
            user_id=payload.user_id,
            user_mode=user_mode,  # ✅ NEW: Pass user mode
            session_history=payload.session_history.dict() if payload.session_history else None,
            consistency=payload.consistency,
            min_prompts_for_assignment=min_prompts,  # ✅ NEW: Configurable
            cold_start_threshold=cold_threshold,     # ✅ NEW: Configurable
            fallback_threshold=fallback_threshold    # ✅ NEW: Configurable
        )
        return result
    except Exception as e:
        return {"error": str(e), "status": "ERROR"}