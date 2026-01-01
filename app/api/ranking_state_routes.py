# app/api/ranking_state_routes.py

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


# Dependency
def get_ranking_service(db: Session = Depends(get_db)) -> RankingStateService:
    return RankingStateService(db)


# Helper function to convert model to response
def to_response(state) -> dict:
    """Convert RankingState model to response dict"""
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


# ==================== CRUD Routes ====================

@router.post("/", response_model=RankingStateResponse, status_code=status.HTTP_201_CREATED)
def create_ranking_state(
    state_data: RankingStateCreateRequest,
    service: RankingStateService = Depends(get_ranking_service)
):
    """Create a new ranking state"""
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
    """Get ranking state by ID"""
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
    """Get ranking state by user and profile"""
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
    """Update ranking state"""
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
    """Delete ranking state"""
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


# ==================== Score Observation Routes ====================

@router.post("/user/{user_id}/profile/{profile_id}/observe", response_model=RankingStateResponse)
def add_score_observation(
    user_id: str,
    profile_id: str,
    score_data: ScoreUpdateRequest,
    service: RankingStateService = Depends(get_ranking_service)
):
    """Add a new score observation and update statistics"""
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


# ==================== Analytics Routes ====================

@router.get("/user/{user_id}/top-profiles", response_model=List[RankingStateResponse])
def get_top_profiles(
    user_id: str,
    limit: int = Query(5, ge=1, le=20),
    service: RankingStateService = Depends(get_ranking_service)
):
    """Get top N profiles for a user"""
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
    """Get summary statistics for a user"""
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
    """Get ranking history for a profile"""
    try:
        return service.get_profile_ranking_history(user_id, profile_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==================== Drift Detection Routes ====================

@router.get("/user/{user_id}/profile/{profile_id}/drift", response_model=DriftDetectionResponse)
def detect_drift(
    user_id: str,
    profile_id: str,
    top_threshold: int = Query(3, ge=1),
    drop_threshold: int = Query(3, ge=1),
    service: RankingStateService = Depends(get_ranking_service)
):
    """Detect drift signals for a user-profile combination"""
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
    """Get all ranking states with drift signals for a user"""
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
    """Reset drift counters for a ranking state"""
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


# ==================== Batch Operations ====================

@router.delete("/user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_user_states(
    user_id: str,
    service: RankingStateService = Depends(get_ranking_service)
):
    """Delete all ranking states for a user"""
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
    """Compare multiple profiles for a user"""
    try:
        return service.compare_profiles(user_id, profile_ids)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )