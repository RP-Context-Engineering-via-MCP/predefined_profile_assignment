"""Ranking State API Routes Module.

This module provides RESTful API endpoints for ranking state management:
- CRUD operations for user-profile ranking states
- Score observation tracking and statistical updates
- Analytics endpoints for top profiles and user statistics
- Drift detection for identifying behavioral inconsistencies
- Batch operations for multi-profile comparisons

Ranking states track how well users match predefined profiles over time,
enabling adaptive profile assignment and drift detection.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.ranking_state_service import RankingStateService
from app.schemas.ranking_state_dto import (
    RankingStateCreateRequest,
    RankingStateUpdateRequest,
    RankingStateResponse,
    RankingStateListResponse,
    ScoreUpdateRequest,
    RankingStatsSummary,
    DriftDetectionResponse,
    ProfileRankingHistory
)
from typing import List


router = APIRouter(
    prefix="/api/ranking-states",
    tags=["ranking-states"]
)


def get_ranking_service(db: Session = Depends(get_db)) -> RankingStateService:
    """Dependency injection for RankingStateService.
    
    Args:
        db: Database session injected by FastAPI.
        
    Returns:
        RankingStateService: Configured ranking state service instance.
    """
    return RankingStateService(db)


def to_response(state) -> dict:
    """Convert RankingState ORM model to response dictionary.
    
    Args:
        state: RankingState ORM model instance.
        
    Returns:
        dict: Ranking state data formatted for API response with all fields serialized.
    """
    return {
        "id": state.id,
        "user_id": state.user_id,
        "profile_id": state.profile_id,
        "cumulative_score": state.cumulative_score,
        "average_score": state.average_score,
        "max_score": state.max_score,
        "observation_count": state.observation_count,
        "last_rank": state.last_rank,
        "consecutive_top_count": state.consecutive_top_count,
        "consecutive_drop_count": state.consecutive_drop_count,
        "updated_at": state.updated_at
    }


@router.post("/", response_model=RankingStateResponse, status_code=status.HTTP_201_CREATED)
def create_ranking_state(
    state_data: RankingStateCreateRequest,
    service: RankingStateService = Depends(get_ranking_service)
):
    """Create new ranking state for user-profile combination.
    
    Initializes tracking state for monitoring how well a user matches a specific
    predefined profile. Used when profile assignment begins.
    
    Args:
        state_data: Initial ranking state data (user_id, profile_id).
        service: Injected RankingStateService dependency.
        
    Returns:
        RankingStateResponse: Created ranking state with initialized statistics.
        
    Raises:
        HTTPException 400: If validation fails or state already exists.
        HTTPException 500: If creation fails.
    """
    try:
        state = service.create_ranking_state(state_data)
        return to_response(state)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ranking state: {str(e)}"
        )


@router.get("/{state_id}", response_model=RankingStateResponse)
def get_ranking_state(
    state_id: str,
    service: RankingStateService = Depends(get_ranking_service)
):
    """Retrieve ranking state by unique identifier.
    
    Args:
        state_id: Unique ranking state identifier (UUID).
        service: Injected RankingStateService dependency.
        
    Returns:
        RankingStateResponse: Complete ranking state data with statistics.
        
    Raises:
        HTTPException 404: If ranking state does not exist.
    """
    state = service.get_ranking_state_by_id(state_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ranking state {state_id} not found"
        )
    return to_response(state)


@router.get("/user/{user_id}/profile/{profile_id}", response_model=RankingStateResponse)
def get_ranking_state_by_user_profile(
    user_id: str,
    profile_id: str,
    service: RankingStateService = Depends(get_ranking_service)
):
    """Retrieve ranking state for specific user-profile combination.
    
    Args:
        user_id: Unique user identifier.
        profile_id: Unique predefined profile identifier.
        service: Injected RankingStateService dependency.
        
    Returns:
        RankingStateResponse: Ranking state for the user-profile pair.
        
    Raises:
        HTTPException 404: If ranking state does not exist for this combination.
    """
    state = service.get_ranking_state_by_user_profile(user_id, profile_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No ranking state found for user {user_id} and profile {profile_id}"
        )
    return to_response(state)


@router.get("/user/{user_id}", response_model=RankingStateListResponse)
def get_all_states_for_user(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: RankingStateService = Depends(get_ranking_service)
):
    """Get all ranking states for a user"""
    try:
        states, total = service.get_all_states_for_user(user_id, skip, limit)
        state_responses = [to_response(state) for state in states]
        return RankingStateListResponse(total=total, states=state_responses)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/profile/{profile_id}", response_model=RankingStateListResponse)
def get_all_states_for_profile(
    profile_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: RankingStateService = Depends(get_ranking_service)
):
    """Get all ranking states for a profile"""
    try:
        states, total = service.get_all_states_for_profile(profile_id, skip, limit)
        state_responses = [to_response(state) for state in states]
        return RankingStateListResponse(total=total, states=state_responses)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{state_id}", response_model=RankingStateResponse)
def update_ranking_state(
    state_id: str,
    state_data: RankingStateUpdateRequest,
    service: RankingStateService = Depends(get_ranking_service)
):
    """Update ranking state statistics manually.
    
    Allows manual adjustment of ranking state fields. Typically used for
    administrative corrections or batch updates.
    
    Args:
        state_id: Unique ranking state identifier.
        state_data: Updated ranking state fields.
        service: Injected RankingStateService dependency.
        
    Returns:
        RankingStateResponse: Updated ranking state data.
        
    Raises:
        HTTPException 400: If validation fails.
        HTTPException 404: If ranking state does not exist.
        HTTPException 500: If update operation fails.
    """
    try:
        state = service.update_ranking_state(state_id, state_data)
        return to_response(state)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update ranking state: {str(e)}"
        )


@router.delete("/{state_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ranking_state(
    state_id: str,
    service: RankingStateService = Depends(get_ranking_service)
):
    """Delete ranking state permanently.
    
    Removes ranking state from database. This operation is irreversible.
    
    Args:
        state_id: Unique ranking state identifier.
        service: Injected RankingStateService dependency.
        
    Returns:
        None: No content on successful deletion (204 status).
        
    Raises:
        HTTPException 404: If ranking state does not exist.
        HTTPException 500: If deletion operation fails.
    """
    try:
        service.delete_ranking_state(state_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete ranking state: {str(e)}"
        )


@router.post("/user/{user_id}/profile/{profile_id}/observe", response_model=RankingStateResponse)
def add_score_observation(
    user_id: str,
    profile_id: str,
    score_data: ScoreUpdateRequest,
    service: RankingStateService = Depends(get_ranking_service)
):
    """Add new score observation and update ranking statistics.
    
    Records new matching score for user-profile combination and automatically
    recalculates cumulative score, average, max, and observation count.
    
    Args:
        user_id: Unique user identifier.
        profile_id: Unique predefined profile identifier.
        score_data: New score observation data.
        service: Injected RankingStateService dependency.
        
    Returns:
        RankingStateResponse: Updated ranking state with recalculated statistics.
        
    Raises:
        HTTPException 400: If score validation fails.
        HTTPException 500: If observation recording fails.
    """
    try:
        state = service.add_score_observation(user_id, profile_id, score_data)
        return to_response(state)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add observation: {str(e)}"
        )


@router.get("/user/{user_id}/top-profiles", response_model=List[RankingStateResponse])
def get_top_profiles(
    user_id: str,
    limit: int = Query(5, ge=1, le=20),
    service: RankingStateService = Depends(get_ranking_service)
):
    """Retrieve top N best-matching profiles for user.
    
    Returns profiles ranked by average score (highest first), showing which
    profiles best match the user's behavioral patterns.
    
    Args:
        user_id: Unique user identifier.
        limit: Maximum number of profiles to return (default: 5, max: 20).
        service: Injected RankingStateService dependency.
        
    Returns:
        List[RankingStateResponse]: Top N ranking states ordered by average score.
        
    Raises:
        HTTPException 500: If ranking retrieval fails.
    """
    try:
        states = service.get_top_profiles_for_user(user_id, limit)
        return [to_response(state) for state in states]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/user/{user_id}/stats", response_model=RankingStatsSummary)
def get_user_stats_summary(
    user_id: str,
    service: RankingStateService = Depends(get_ranking_service)
):
    """Retrieve summary statistics for user's profile rankings.
    
    Provides aggregated statistics including total profiles evaluated,
    highest average score, best-matching profile, and overall trends.
    
    Args:
        user_id: Unique user identifier.
        service: Injected RankingStateService dependency.
        
    Returns:
        RankingStatsSummary: Comprehensive statistical summary.
        
    Raises:
        HTTPException 500: If statistics calculation fails.
    """
    try:
        return service.get_user_stats_summary(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/user/{user_id}/profile/{profile_id}/history", response_model=ProfileRankingHistory)
def get_profile_history(
    user_id: str,
    profile_id: str,
    service: RankingStateService = Depends(get_ranking_service)
):
    """Retrieve ranking history for specific user-profile combination.
    
    Returns historical ranking data showing how the user's compatibility with
    this profile has evolved over time.
    
    Args:
        user_id: Unique user identifier.
        profile_id: Unique predefined profile identifier.
        service: Injected RankingStateService dependency.
        
    Returns:
        ProfileRankingHistory: Historical ranking data with timestamps.
        
    Raises:
        HTTPException 404: If ranking state does not exist.
        HTTPException 500: If history retrieval fails.
    """
    try:
        return service.get_profile_ranking_history(user_id, profile_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/user/{user_id}/profile/{profile_id}/drift", response_model=DriftDetectionResponse)
def detect_drift(
    user_id: str,
    profile_id: str,
    top_threshold: int = Query(3, ge=1),
    drop_threshold: int = Query(3, ge=1),
    service: RankingStateService = Depends(get_ranking_service)
):
    """Detect behavioral drift for user-profile combination.
    
    Identifies drift signals indicating user behavior is no longer consistent
    with assigned profile. Checks consecutive top/drop counts against thresholds.
    
    Args:
        user_id: Unique user identifier.
        profile_id: Unique predefined profile identifier.
        top_threshold: Consecutive top rank threshold for drift signal (default: 3).
        drop_threshold: Consecutive drop rank threshold for drift signal (default: 3).
        service: Injected RankingStateService dependency.
        
    Returns:
        DriftDetectionResponse: Drift detection result with signal flags and counters.
        
    Raises:
        HTTPException 404: If ranking state does not exist.
        HTTPException 500: If drift detection fails.
    """
    try:
        return service.detect_drift(user_id, profile_id, top_threshold, drop_threshold)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/user/{user_id}/drift-states", response_model=List[RankingStateResponse])
def get_drift_states(
    user_id: str,
    top_threshold: int = Query(3, ge=1),
    drop_threshold: int = Query(3, ge=1),
    service: RankingStateService = Depends(get_ranking_service)
):
    """Retrieve all ranking states with drift signals for user.
    
    Returns all user-profile combinations showing drift signals, indicating
    behavioral inconsistencies requiring attention.
    
    Args:
        user_id: Unique user identifier.
        top_threshold: Consecutive top rank threshold for drift signal (default: 3).
        drop_threshold: Consecutive drop rank threshold for drift signal (default: 3).
        service: Injected RankingStateService dependency.
        
    Returns:
        List[RankingStateResponse]: Ranking states exhibiting drift signals.
        
    Raises:
        HTTPException 500: If drift state retrieval fails.
    """
    try:
        states = service.get_all_drift_states_for_user(user_id, top_threshold, drop_threshold)
        return [to_response(state) for state in states]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{state_id}/reset-drift", response_model=RankingStateResponse)
def reset_drift_counters(
    state_id: str,
    service: RankingStateService = Depends(get_ranking_service)
):
    """Reset drift counters for ranking state.
    
    Clears consecutive_top_count and consecutive_drop_count, typically used
    after addressing drift or reassigning profile.
    
    Args:
        state_id: Unique ranking state identifier.
        service: Injected RankingStateService dependency.
        
    Returns:
        RankingStateResponse: Updated ranking state with reset counters.
        
    Raises:
        HTTPException 404: If ranking state does not exist.
        HTTPException 500: If reset operation fails.
    """
    try:
        state = service.reset_drift_counters(state_id)
        return to_response(state)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset drift counters: {str(e)}"
        )


@router.delete("/user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_user_states(
    user_id: str,
    service: RankingStateService = Depends(get_ranking_service)
):
    """Delete all ranking states for user.
    
    Removes all profile ranking states for the specified user. Typically used
    when user account is deleted or reset. This operation is irreversible.
    
    Args:
        user_id: Unique user identifier.
        service: Injected RankingStateService dependency.
        
    Returns:
        None: No content on successful deletion (204 status).
        
    Raises:
        HTTPException 404: If user has no ranking states.
        HTTPException 500: If deletion operation fails.
    """
    try:
        count = service.delete_all_states_for_user(user_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user states: {str(e)}"
        )


@router.get("/user/{user_id}/compare", response_model=List[dict])
def compare_profiles(
    user_id: str,
    profile_ids: List[str] = Query(...),
    service: RankingStateService = Depends(get_ranking_service)
):
    """Compare multiple profiles for user side-by-side.
    
    Provides comparative analysis of specified profiles showing relative scores,
    statistics, and compatibility metrics for decision-making.
    
    Args:
        user_id: Unique user identifier.
        profile_ids: List of profile IDs to compare.
        service: Injected RankingStateService dependency.
        
    Returns:
        List[dict]: Comparison data for each profile with unified metrics.
        
    Raises:
        HTTPException 500: If comparison operation fails.
    """
    try:
        return service.compare_profiles(user_id, profile_ids)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )