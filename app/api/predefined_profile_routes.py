"""Predefined Profile Assignment API Routes Module.

This module provides RESTful API endpoints for profile assignment operations:
- Retrieving user profile assignment status with aggregated rankings
- Assigning profiles based on extracted behavior data
- Supporting both COLD_START and DRIFT_FALLBACK user modes
- Providing full profile context for downstream services

Profile assignment uses behavioral signals to match users with predefined
profiles based on complexity, consistency, and behavioral compatibility.
Also updates user domain expertise state based on behavior signals.

Endpoints:
- GET /: List all predefined profiles with full context
- GET /{profile_id}: Get single profile with full context
- POST /assign-profile: Async endpoint using IntakeOrchestrator (preferred)
- GET /user/{user_id}: Get current assignment status
- POST /assign-profile/sync: Legacy sync endpoint for backward compatibility
"""

import json
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path
from app.services.profile_assigner import ProfileAssigner
from app.services.domain_expertise_service import DomainExpertiseService
from app.repositories.predefined_profile_repo import PredefinedProfileRepository
from app.schemas.predefined_profile_dto import (
    BehaviorInputDTO, 
    AssignProfileRequest,
    AssignmentStatusResponse,
    ProfileContextResponse,
    ProfileListResponse
)
from app.core.database import get_db
from app.core.intake_orchestrator import IntakeOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/predefined-profiles",
    tags=["profile-assignment"]
)

# Shared orchestrator instance for async endpoints
_orchestrator = IntakeOrchestrator()


def _profile_to_context_response(profile) -> ProfileContextResponse:
    """Convert Profile ORM model to ProfileContextResponse DTO.
    
    Extracts AI context fields for LLM personalization.
    
    Args:
        profile: Profile SQLAlchemy model
        
    Returns:
        ProfileContextResponse with AI context attributes populated
    """
    # Parse JSON array fields (stored as text in database)
    def parse_json_array(value: str) -> list:
        if not value:
            return []
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
    
    return ProfileContextResponse(
        profile_id=profile.profile_id,
        profile_name=profile.profile_name,
        context_statement=profile.context_statement,
        assumptions=parse_json_array(profile.assumptions),
        ai_guidance=parse_json_array(profile.ai_guidance),
        preferred_response_style=parse_json_array(profile.preferred_response_style),
        context_injection_prompt=profile.context_injection_prompt
    )


# =============================================================================
# Profile Context Endpoints - For downstream services
# =============================================================================

@router.get("/", response_model=ProfileListResponse)
def get_all_profiles(db=Depends(get_db)):
    """Get all predefined profiles with full context.
    
    Returns complete profile information including intents, interests,
    behavior levels, signals, output preferences, and interaction tones.
    Used by downstream services (LLM Orchestration, Recommendation Engine)
    to understand profile characteristics.
    
    Returns:
        ProfileListResponse: List of all profiles with full context
        
    Raises:
        HTTPException 500: If profile retrieval fails
    """
    logger.debug("GET / - Retrieving all predefined profiles with context")
    
    try:
        repo = PredefinedProfileRepository(db)
        profiles = repo.get_all_profiles_with_context()
        
        profile_responses = [
            _profile_to_context_response(profile)
            for profile in profiles
        ]
        
        logger.debug(f"GET / - Success: returning {len(profile_responses)} profiles")
        return ProfileListResponse(
            profiles=profile_responses,
            total=len(profile_responses)
        )
    except Exception as e:
        logger.error(f"GET / - Error retrieving profiles: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{profile_id}", response_model=ProfileContextResponse)
def get_profile_by_id(
    profile_id: str = Path(..., description="Profile ID (e.g., P1, P2, P3)"),
    db=Depends(get_db)
):
    """Get a single profile by ID with full context.
    
    Returns complete profile information including intents, interests,
    behavior levels, signals, output preferences, and interaction tones.
    Used by downstream services to adapt behavior based on assigned profile.
    
    Args:
        profile_id: Profile identifier (P1-P6)
        db: Database session dependency
        
    Returns:
        ProfileContextResponse: Full profile context
        
    Raises:
        HTTPException 404: If profile not found
        HTTPException 500: If profile retrieval fails
    """
    logger.debug(f"GET /{profile_id} - Retrieving profile context")
    
    try:
        repo = PredefinedProfileRepository(db)
        profile = repo.get_profile_by_id(profile_id)
        
        if not profile:
            logger.warning(f"GET /{profile_id} - Profile not found")
            raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")
        
        response = _profile_to_context_response(profile)
        logger.debug(f"GET /{profile_id} - Success: {profile.profile_name}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET /{profile_id} - Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Profile Assignment Endpoints
# =============================================================================

@router.post("/assign-profile")
async def assign_profile(request: AssignProfileRequest):
    """Assign predefined profile based on extracted behavior data (async).
    
    Called by Behavior Resolution Mechanism after each prompt (cold start)
    or by Drift Detection Service (drift fallback). Uses IntakeOrchestrator
    to process assignment and publish events to downstream services.
    
    Args:
        request: AssignProfileRequest containing:
            - user_id: Unique user identifier
            - mode: "COLD_START" or "DRIFT_FALLBACK"
            - extracted_behavior: Single dict (COLD_START) or list of dicts (DRIFT_FALLBACK)
            - trigger_event_id: Drift event ID if mode is DRIFT_FALLBACK
        
    Returns:
        dict: Assignment result containing:
            - status: "ASSIGNED" or "PENDING"
            - confidence_level: "HIGH", "MEDIUM", or "LOW"
            - user_mode: Mode used for assignment
            - prompt_count: Total prompts processed
            - assigned_profile_id: Selected profile or None
            - aggregated_rankings: Scores for all profiles
        
    Raises:
        HTTPException 400: If user_id missing or behavior format invalid for mode.
        HTTPException 404: If user not found in database.
        HTTPException 500: If profile assignment process fails.
    """
    logger.debug(
        f"POST /assign-profile - user_id={request.user_id}, mode={request.mode}, "
        f"trigger_event_id={request.trigger_event_id}, behavior_type={type(request.extracted_behavior).__name__}"
    )
    
    if not request.user_id:
        logger.warning("POST /assign-profile - Missing user_id in request")
        raise HTTPException(
            status_code=400, 
            detail="user_id is required for profile assignment"
        )
    
    try:
        result = await _orchestrator.process(
            user_id=request.user_id,
            mode=request.mode,
            extracted_behavior=request.extracted_behavior,
            trigger_event_id=request.trigger_event_id
        )
        logger.debug(
            f"POST /assign-profile - Success: user_id={request.user_id}, "
            f"status={result.get('status')}, assigned_profile={result.get('assigned_profile_id')}"
        )
        return result
    except ValueError as e:
        logger.warning(f"POST /assign-profile - User not found: user_id={request.user_id}, error={e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"POST /assign-profile - Error: user_id={request.user_id}, error={e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}")
async def get_profile_assignment_status(
    user_id: str = Path(..., description="User ID to retrieve profile assignment status")
):
    """Retrieve current profile assignment status for user.
    
    Provides comprehensive profile assignment information including assigned profile,
    confidence levels, and aggregated rankings across all predefined profiles.
    Does not trigger any scoring - read-only operation.
    
    Args:
        user_id: Unique user identifier.
        
    Returns:
        AssignmentStatusResponse: Profile assignment status containing:
            - status: "ASSIGNED", "PENDING", or "NOT_FOUND"
            - confidence_level: Assignment confidence level
            - user_mode: Current profile mode
            - prompt_count: Total prompts processed
            - assigned_profile_id: Currently assigned profile
            - aggregated_rankings: Scores for all profiles
        
    Raises:
        HTTPException 404: If user not found.
        HTTPException 500: If status retrieval fails.
    """
    logger.debug(f"GET /user/{user_id} - Retrieving profile assignment status")
    
    try:
        result = await _orchestrator.get_status(user_id=user_id)
        if result.get("status") == "NOT_FOUND":
            logger.warning(f"GET /user/{user_id} - User not found in database")
            raise HTTPException(status_code=404, detail="User not found")
        logger.debug(
            f"GET /user/{user_id} - Success: status={result.get('status')}, "
            f"assigned_profile={result.get('assigned_profile_id')}, mode={result.get('user_mode')}"
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET /user/{user_id} - Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Legacy Sync Endpoints (for backward compatibility)
# =============================================================================

@router.post("/assign-profile/sync")
def assign_profile_sync(payload: BehaviorInputDTO, db=Depends(get_db)):
    """Assign predefined profile based on extracted behavior data (sync/legacy).
    
    Legacy synchronous endpoint. Use POST /assign-profile for new integrations.
    
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
    logger.debug(
        f"POST /assign-profile/sync - user_id={payload.user_id}, "
        f"behavior_type={type(payload.behavior).__name__}"
    )
    
    if not payload.user_id:
        logger.warning("POST /assign-profile/sync - Missing user_id in request")
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
        
        logger.debug(
            f"POST /assign-profile/sync - Success: user_id={payload.user_id}, "
            f"assigned_profile={result.get('assigned_profile_id')}"
        )
        return result
    except ValueError as e:
        logger.warning(f"POST /assign-profile/sync - User not found: user_id={payload.user_id}, error={e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"POST /assign-profile/sync - Error: user_id={payload.user_id}, error={e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/sync")
def get_profile_assignment_status_sync(
    user_id: str = Path(..., description="User ID to retrieve profile assignment status"),
    db=Depends(get_db)
):
    """Retrieve current profile assignment status for user (sync/legacy).
    
    Legacy synchronous endpoint. Use GET /user/{user_id} for new integrations.
    
    Args:
        user_id: Unique user identifier.
        db: Database session dependency.
        
    Returns:
        dict: Profile assignment status.
        
    Raises:
        HTTPException 500: If status retrieval fails.
    """
    logger.debug(f"GET /user/{user_id}/sync - Retrieving profile assignment status")
    
    assigner = ProfileAssigner(db)
    
    try:
        result = assigner.get_assignment_status(user_id=user_id)
        logger.debug(
            f"GET /user/{user_id}/sync - Success: status={result.get('status')}, "
            f"assigned_profile={result.get('assigned_profile_id')}"
        )
        return result
    except Exception as e:
        logger.error(f"GET /user/{user_id}/sync - Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))