# app/repositories/ranking_state_repo.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, desc, asc
from app.models.user_profile_ranking_state import UserProfileRankingState
from datetime import datetime
from typing import List, Optional, Tuple
import uuid


class RankingStateRepository:
    """Repository for UserProfileRankingState CRUD operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_ranking_state(
        self,
        user_id: str,
        profile_id: str,
        cumulative_score: float = 0.0,
        average_score: float = 0.0,
        max_score: float = 0.0,
        observation_count: int = 0,
        last_rank: int = 0,
        consecutive_top_count: int = 0,
        consecutive_drop_count: int = 0
    ) -> UserProfileRankingState:
        """
        Create a new ranking state
        
        Args:
            user_id: User ID
            profile_id: Profile ID
            cumulative_score: Total cumulative score
            average_score: Average score
            max_score: Maximum score recorded
            observation_count: Number of observations
            last_rank: Last recorded rank
            consecutive_top_count: Count of consecutive top rankings
            consecutive_drop_count: Count of consecutive rank drops
            
        Returns:
            UserProfileRankingState: Created ranking state
            
        Raises:
            ValueError: If user-profile combination already exists
        """
        try:
            state = UserProfileRankingState(
                id=str(uuid.uuid4()),
                user_id=user_id,
                profile_id=profile_id,
                cumulative_score=cumulative_score,
                average_score=average_score,
                max_score=max_score,
                observation_count=observation_count,
                last_rank=last_rank,
                consecutive_top_count=consecutive_top_count,
                consecutive_drop_count=consecutive_drop_count
            )
            self.db.add(state)
            self.db.commit()
            self.db.refresh(state)
            return state
        except IntegrityError:
            self.db.rollback()
            raise ValueError(
                f"Ranking state for user {user_id} and profile {profile_id} already exists"
            )

    def get_ranking_state_by_id(self, state_id: str) -> Optional[UserProfileRankingState]:
        """Get ranking state by ID"""
        return self.db.query(UserProfileRankingState).filter(
            UserProfileRankingState.id == state_id
        ).first()

    def get_ranking_state_by_user_profile(
        self,
        user_id: str,
        profile_id: str
    ) -> Optional[UserProfileRankingState]:
        """Get ranking state by user and profile combination"""
        return self.db.query(UserProfileRankingState).filter(
            and_(
                UserProfileRankingState.user_id == user_id,
                UserProfileRankingState.profile_id == profile_id
            )
        ).first()

    def get_all_states_for_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[UserProfileRankingState], int]:
        """
        Get all ranking states for a specific user
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (states list, total count)
        """
        query = self.db.query(UserProfileRankingState).filter(
            UserProfileRankingState.user_id == user_id
        ).order_by(desc(UserProfileRankingState.average_score))
        
        total = query.count()
        states = query.offset(skip).limit(limit).all()
        return states, total

    def get_all_states_for_profile(
        self,
        profile_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[UserProfileRankingState], int]:
        """
        Get all ranking states for a specific profile across users
        
        Args:
            profile_id: Profile ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (states list, total count)
        """
        query = self.db.query(UserProfileRankingState).filter(
            UserProfileRankingState.profile_id == profile_id
        ).order_by(desc(UserProfileRankingState.average_score))
        
        total = query.count()
        states = query.offset(skip).limit(limit).all()
        return states, total

    def get_top_ranked_profiles_for_user(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[UserProfileRankingState]:
        """Get top N ranked profiles for a user based on average score"""
        return self.db.query(UserProfileRankingState).filter(
            UserProfileRankingState.user_id == user_id
        ).order_by(
            desc(UserProfileRankingState.average_score),
            asc(UserProfileRankingState.last_rank)
        ).limit(limit).all()

    def update_ranking_state(
        self,
        state_id: str,
        **kwargs
    ) -> UserProfileRankingState:
        """
        Update ranking state fields
        
        Args:
            state_id: Ranking state ID
            **kwargs: Fields to update
            
        Returns:
            UserProfileRankingState: Updated ranking state
        """
        state = self.get_ranking_state_by_id(state_id)
        if not state:
            raise ValueError(f"Ranking state with id {state_id} not found")

        update_data = {}
        allowed_fields = [
            'cumulative_score', 'average_score', 'max_score',
            'observation_count', 'last_rank',
            'consecutive_top_count', 'consecutive_drop_count'
        ]

        for field in allowed_fields:
            if field in kwargs and kwargs[field] is not None:
                update_data[field] = kwargs[field]

        if not update_data:
            raise ValueError("No fields to update")

        try:
            for key, value in update_data.items():
                setattr(state, key, value)
            
            state.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(state)
            return state
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to update ranking state: {str(e)}")

    def add_observation(
        self,
        user_id: str,
        profile_id: str,
        new_score: float,
        new_rank: int
    ) -> UserProfileRankingState:
        """
        Add a new observation and update aggregated statistics
        
        CORRECTED: Drift counter logic aligned with fullplan.txt
        - rank == 1 → increment consecutive_top_count, reset consecutive_drop_count
        - rank != 1 → increment consecutive_drop_count, reset consecutive_top_count
        
        Args:
            user_id: User ID
            profile_id: Profile ID
            new_score: New score to add
            new_rank: New rank position
            
        Returns:
            UserProfileRankingState: Updated ranking state
        """
        state = self.get_ranking_state_by_user_profile(user_id, profile_id)
        
        if not state:
            # Create new state if doesn't exist
            state = self.create_ranking_state(
                user_id=user_id,
                profile_id=profile_id,
                cumulative_score=new_score,
                average_score=new_score,
                max_score=new_score,
                observation_count=1,
                last_rank=new_rank,
                consecutive_top_count=1 if new_rank == 1 else 0,
                consecutive_drop_count=0
            )
            return state

        # Update existing state
        state.observation_count += 1
        state.cumulative_score += new_score
        state.average_score = state.cumulative_score / state.observation_count
        state.max_score = max(state.max_score, new_score)

        # ✅ CORRECTED: Simplified drift logic per fullplan.txt
        if new_rank == 1:
            # Profile is ranked #1
            state.consecutive_top_count += 1
            state.consecutive_drop_count = 0
        else:
            # Profile is NOT #1 (any rank > 1)
            state.consecutive_drop_count += 1
            state.consecutive_top_count = 0

        state.last_rank = new_rank
        state.updated_at = datetime.utcnow()

        try:
            self.db.commit()
            self.db.refresh(state)
            return state
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to add observation: {str(e)}")

    def delete_ranking_state(self, state_id: str) -> bool:
        """
        Delete a ranking state
        
        Args:
            state_id: Ranking state ID
            
        Returns:
            bool: True if deletion was successful
        """
        state = self.get_ranking_state_by_id(state_id)
        if not state:
            raise ValueError(f"Ranking state with id {state_id} not found")

        try:
            self.db.delete(state)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to delete ranking state: {str(e)}")

    def delete_all_states_for_user(self, user_id: str) -> int:
        """Delete all ranking states for a user"""
        try:
            count = self.db.query(UserProfileRankingState).filter(
                UserProfileRankingState.user_id == user_id
            ).delete()
            self.db.commit()
            return count
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to delete user ranking states: {str(e)}")

    def get_states_with_drift(
        self,
        user_id: str,
        top_threshold: int = 3,
        drop_threshold: int = 3
    ) -> List[UserProfileRankingState]:
        """
        Get ranking states showing drift signals
        
        Args:
            user_id: User ID
            top_threshold: Minimum consecutive top counts to consider drift
            drop_threshold: Minimum consecutive drop counts to consider drift
            
        Returns:
            List of ranking states with drift signals
        """
        return self.db.query(UserProfileRankingState).filter(
            and_(
                UserProfileRankingState.user_id == user_id,
                (
                    (UserProfileRankingState.consecutive_top_count >= top_threshold) |
                    (UserProfileRankingState.consecutive_drop_count >= drop_threshold)
                )
            )
        ).all()

    def reset_drift_counters(self, state_id: str) -> UserProfileRankingState:
        """Reset drift counters for a ranking state"""
        state = self.get_ranking_state_by_id(state_id)
        if not state:
            raise ValueError(f"Ranking state with id {state_id} not found")

        state.consecutive_top_count = 0
        state.consecutive_drop_count = 0
        state.updated_at = datetime.utcnow()

        try:
            self.db.commit()
            self.db.refresh(state)
            return state
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to reset drift counters: {str(e)}")