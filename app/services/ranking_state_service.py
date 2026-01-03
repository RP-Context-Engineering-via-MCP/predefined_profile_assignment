# app/services/ranking_state_service.py

from sqlalchemy.orm import Session
from app.repositories.ranking_state_repo import RankingStateRepository
from app.schemas.ranking_state_dto import (
    RankingStateCreateRequest,
    RankingStateUpdateRequest,
    ScoreUpdateRequest,
    RankingStatsSummary,
    DriftDetectionResponse,
    ProfileRankingHistory
)
from app.models.user_profile_ranking_state import UserProfileRankingState
from typing import List, Optional, Tuple
from datetime import datetime


class RankingStateService:
    """Service layer for ranking state business logic"""

    def __init__(self, db: Session):
        self.repo = RankingStateRepository(db)

    def create_ranking_state(
        self,
        state_data: RankingStateCreateRequest
    ) -> UserProfileRankingState:
        """
        Create a new ranking state
        
        Args:
            state_data: Ranking state creation data
            
        Returns:
            UserProfileRankingState: Created ranking state
        """
        return self.repo.create_ranking_state(
            user_id=state_data.user_id,
            profile_id=state_data.profile_id,
            cumulative_score=state_data.cumulative_score,
            average_score=state_data.average_score,
            max_score=state_data.max_score,
            observation_count=state_data.observation_count,
            last_rank=state_data.last_rank,
            consecutive_top_count=state_data.consecutive_top_count,
            consecutive_drop_count=state_data.consecutive_drop_count
        )

    def get_ranking_state_by_id(
        self,
        state_id: str
    ) -> Optional[UserProfileRankingState]:
        """Get ranking state by ID"""
        return self.repo.get_ranking_state_by_id(state_id)

    def get_ranking_state_by_user_profile(
        self,
        user_id: str,
        profile_id: str
    ) -> Optional[UserProfileRankingState]:
        """Get ranking state by user and profile"""
        return self.repo.get_ranking_state_by_user_profile(user_id, profile_id)

    def get_all_states_for_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[UserProfileRankingState], int]:
        """Get all ranking states for a user"""
        return self.repo.get_all_states_for_user(user_id, skip, limit)

    def get_all_states_for_profile(
        self,
        profile_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[UserProfileRankingState], int]:
        """Get all ranking states for a profile"""
        return self.repo.get_all_states_for_profile(profile_id, skip, limit)

    def update_ranking_state(
        self,
        state_id: str,
        state_data: RankingStateUpdateRequest
    ) -> UserProfileRankingState:
        """Update ranking state"""
        update_dict = {k: v for k, v in state_data.dict().items() if v is not None}
        
        if not update_dict:
            raise ValueError("No fields to update")
        
        return self.repo.update_ranking_state(state_id, **update_dict)

    def add_score_observation(
        self,
        user_id: str,
        profile_id: str,
        score_data: ScoreUpdateRequest
    ) -> UserProfileRankingState:
        """
        Add a new score observation and update statistics
        
        Args:
            user_id: User ID
            profile_id: Profile ID
            score_data: New score and rank data
            
        Returns:
            UserProfileRankingState: Updated ranking state
        """
        return self.repo.add_observation(
            user_id=user_id,
            profile_id=profile_id,
            new_score=score_data.new_score,
            new_rank=score_data.new_rank
        )

    def update_from_ranked_profiles(
        self,
        user_id: str,
        ranked_profiles: List[Tuple[str, float]]
    ) -> List[UserProfileRankingState]:
        """
        Update ranking state table using a full ranked profile list
        (called once per prompt)

        Args:
            user_id: User ID
            ranked_profiles: List of (profile_id, score) tuples sorted DESC by score
            
        Returns:
            List of updated ranking states
        """
        updated_states = []
        
        for rank, (profile_id, score) in enumerate(ranked_profiles, start=1):
            try:
                state = self.repo.add_observation(
                    user_id=user_id,
                    profile_id=profile_id,
                    new_score=score,
                    new_rank=rank
                )
                updated_states.append(state)
            except Exception as e:
                # Log error but continue with other observations
                print(f"Error adding observation for profile {profile_id}: {e}")
        
        return updated_states

    def get_top_profiles_for_user(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[UserProfileRankingState]:
        """Get top N profiles for a user"""
        return self.repo.get_top_ranked_profiles_for_user(user_id, limit)

    def get_user_stats_summary(self, user_id: str) -> RankingStatsSummary:
        """
        Get summary statistics for a user's ranking states
        
        Args:
            user_id: User ID
            
        Returns:
            RankingStatsSummary: Summary statistics
        """
        states, total = self.repo.get_all_states_for_user(user_id, limit=1000)
        
        if not states:
            return RankingStatsSummary(
                user_id=user_id,
                total_profiles=0,
                highest_average_score=0.0,
                total_observations=0,
                profiles_with_drift=0
            )
        
        # Find top ranked profile
        top_profile = max(states, key=lambda s: s.average_score)
        
        # Count profiles with drift (using thresholds)
        drift_count = len([
            s for s in states 
            if s.consecutive_top_count >= 3 or s.consecutive_drop_count >= 3
        ])
        
        # Total observations across all profiles
        total_obs = sum(s.observation_count for s in states)
        
        return RankingStatsSummary(
            user_id=user_id,
            total_profiles=total,
            top_ranked_profile_id=top_profile.profile_id,
            highest_average_score=top_profile.average_score,
            total_observations=total_obs,
            profiles_with_drift=drift_count
        )

    def detect_drift(
        self,
        user_id: str,
        profile_id: str,
        top_threshold: int = 3,
        drop_threshold: int = 3
    ) -> DriftDetectionResponse:
        """
        Detect drift signals for a specific user-profile combination
        
        Args:
            user_id: User ID
            profile_id: Profile ID
            top_threshold: Consecutive top count threshold
            drop_threshold: Consecutive drop count threshold
            
        Returns:
            DriftDetectionResponse: Drift detection analysis
        """
        state = self.repo.get_ranking_state_by_user_profile(user_id, profile_id)
        
        if not state:
            raise ValueError(f"No ranking state found for user {user_id} and profile {profile_id}")
        
        has_drift = False
        drift_type = None
        recommendation = "Continue monitoring"
        
        # Per fullplan.txt section 8: Check score degradation first
        DRIFT_CONF_THRESHOLD = 0.50
        if state.average_score < DRIFT_CONF_THRESHOLD:
            has_drift = True
            drift_type = "score_degradation"
            recommendation = "Profile confidence has degraded significantly - consider fallback"
        
        # Check for consistent top performance
        elif state.consecutive_top_count >= top_threshold:
            has_drift = True
            drift_type = "consistent_top"
            recommendation = "Consider switching to DYNAMIC_ONLY mode"
        
        # Check for consistent drops
        elif state.consecutive_drop_count >= drop_threshold:
            has_drift = True
            drift_type = "consistent_drop"
            recommendation = "Consider activating fallback profile"
        
        # Check for volatility
        elif (state.consecutive_top_count > 0 and state.consecutive_drop_count > 0):
            has_drift = True
            drift_type = "volatile"
            recommendation = "Monitor closely, profile may be unstable"
        
        return DriftDetectionResponse(
            user_id=user_id,
            profile_id=profile_id,
            has_drift=has_drift,
            drift_type=drift_type,
            consecutive_top_count=state.consecutive_top_count,
            consecutive_drop_count=state.consecutive_drop_count,
            recommendation=recommendation
        )

    def get_profile_ranking_history(
        self,
        user_id: str,
        profile_id: str
    ) -> ProfileRankingHistory:
        """
        Get ranking history analysis for a profile
        
        Args:
            user_id: User ID
            profile_id: Profile ID
            
        Returns:
            ProfileRankingHistory: Historical ranking information
        """
        state = self.repo.get_ranking_state_by_user_profile(user_id, profile_id)
        
        if not state:
            raise ValueError(f"No ranking state found for user {user_id} and profile {profile_id}")
        
        # Determine score trend
        score_trend = "stable"
        if state.consecutive_top_count >= 2:
            score_trend = "improving"
        elif state.consecutive_drop_count >= 2:
            score_trend = "declining"
        
        return ProfileRankingHistory(
            profile_id=profile_id,
            user_id=user_id,
            current_rank=state.last_rank,
            average_score=state.average_score,
            score_trend=score_trend,
            observation_count=state.observation_count,
            last_updated=state.updated_at
        )

    def get_all_drift_states_for_user(
        self,
        user_id: str,
        top_threshold: int = 3,
        drop_threshold: int = 3
    ) -> List[UserProfileRankingState]:
        """Get all ranking states with drift signals for a user"""
        return self.repo.get_states_with_drift(user_id, top_threshold, drop_threshold)

    def reset_drift_counters(self, state_id: str) -> UserProfileRankingState:
        """Reset drift counters for a ranking state"""
        return self.repo.reset_drift_counters(state_id)

    def delete_ranking_state(self, state_id: str) -> bool:
        """Delete a ranking state"""
        return self.repo.delete_ranking_state(state_id)

    def delete_all_states_for_user(self, user_id: str) -> int:
        """Delete all ranking states for a user"""
        return self.repo.delete_all_states_for_user(user_id)

    def batch_add_observations(
        self,
        user_id: str,
        observations: List[dict]
    ) -> List[UserProfileRankingState]:
        """
        Add multiple observations in batch
        
        Args:
            user_id: User ID
            observations: List of dicts with profile_id, score, and rank
            
        Returns:
            List of updated ranking states
        """
        updated_states = []
        
        for obs in observations:
            try:
                state = self.repo.add_observation(
                    user_id=user_id,
                    profile_id=obs['profile_id'],
                    new_score=obs['score'],
                    new_rank=obs['rank']
                )
                updated_states.append(state)
            except Exception as e:
                # Log error but continue with other observations
                print(f"Error adding observation for profile {obs['profile_id']}: {e}")
        
        return updated_states

    def compare_profiles(
        self,
        user_id: str,
        profile_ids: List[str]
    ) -> List[dict]:
        """
        Compare multiple profiles for a user
        
        Args:
            user_id: User ID
            profile_ids: List of profile IDs to compare
            
        Returns:
            List of comparison data
        """
        comparisons = []
        
        for profile_id in profile_ids:
            state = self.repo.get_ranking_state_by_user_profile(user_id, profile_id)
            
            if state:
                comparisons.append({
                    'profile_id': profile_id,
                    'average_score': state.average_score,
                    'last_rank': state.last_rank,
                    'observation_count': state.observation_count,
                    'has_drift': (
                        state.consecutive_top_count >= 3 or 
                        state.consecutive_drop_count >= 3
                    )
                })
        
        # Sort by average score descending
        comparisons.sort(key=lambda x: x['average_score'], reverse=True)
        
        return comparisons