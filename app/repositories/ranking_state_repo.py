"""Ranking state repository.

Provides data access layer for UserProfileRankingState CRUD operations,
including drift detection, observation tracking, and aggregated statistics.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, desc, asc
from app.models.user_profile_ranking_state import UserProfileRankingState
from datetime import datetime
from typing import List, Optional, Tuple
import uuid


class RankingStateRepository:
    """Ranking state data access repository.
    
    Manages temporal tracking of user-profile matching scores and rankings.
    Implements drift detection through consecutive top/drop counters.
    
    Attributes:
        db: SQLAlchemy database session
    """

    def __init__(self, db: Session):
        """Initialize repository with database session.
        
        Args:
            db: Active SQLAlchemy session
        """
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
        """Create new ranking state for user-profile pair.
        
        Initializes tracking state with default or provided metrics.
        Generates unique UUID identifier.
        
        Args:
            user_id: User unique identifier
            profile_id: Profile unique identifier
            cumulative_score: Initial cumulative score (default 0.0)
            average_score: Initial average score (default 0.0)
            max_score: Initial maximum score (default 0.0)
            observation_count: Initial observation count (default 0)
            last_rank: Initial rank position (default 0)
            consecutive_top_count: Initial consecutive top count (default 0)
            consecutive_drop_count: Initial consecutive drop count (default 0)
            
        Returns:
            Created and persisted UserProfileRankingState object
            
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
        """Retrieve ranking state by unique identifier.
        
        Args:
            state_id: Ranking state UUID
            
        Returns:
            UserProfileRankingState object or None
        """
        return self.db.query(UserProfileRankingState).filter(
            UserProfileRankingState.id == state_id
        ).first()

    def get_ranking_state_by_user_profile(
        self,
        user_id: str,
        profile_id: str
    ) -> Optional[UserProfileRankingState]:
        """Retrieve ranking state by user-profile pair.
        
        Args:
            user_id: User unique identifier
            profile_id: Profile unique identifier
            
        Returns:
            UserProfileRankingState object or None
        """
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
        """Retrieve all ranking states for specific user.
        
        Results ordered by average score descending.
        
        Args:
            user_id: User unique identifier
            skip: Number of records to skip (pagination)
            limit: Maximum records to return
            
        Returns:
            Tuple of (ranking state list, total count)
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
        """Retrieve all ranking states for specific profile.
        
        Shows how different users rank this profile.
        Results ordered by average score descending.
        
        Args:
            profile_id: Profile unique identifier
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            Tuple of (ranking state list, total count)
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
        """Retrieve top N profiles for user.
        
        Ordered by average score (descending), then last rank (ascending).
        
        Args:
            user_id: User unique identifier
            limit: Maximum number of top profiles to return
            
        Returns:
            List of top-ranked UserProfileRankingState objects
        """
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
        """Update ranking state fields.
        
        Supports partial updates. Automatically updates updated_at timestamp.
        
        Args:
            state_id: Ranking state UUID
            **kwargs: Fields to update. Allowed: cumulative_score, average_score,
                max_score, observation_count, last_rank, consecutive_top_count,
                consecutive_drop_count
            
        Returns:
            Updated UserProfileRankingState object
            
        Raises:
            ValueError: If state not found, no fields provided, or update fails
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
        """Add new observation and update aggregated statistics.
        
        Implements drift detection counters:
        - If rank == 1: increment consecutive_top_count, reset consecutive_drop_count
        - If rank != 1: increment consecutive_drop_count, reset consecutive_top_count
        
        Creates new state if user-profile pair doesn't exist.
        
        Args:
            user_id: User unique identifier
            profile_id: Profile unique identifier
            new_score: New matching score
            new_rank: New rank position
            
        Returns:
            Updated UserProfileRankingState object
            
        Raises:
            ValueError: If observation addition fails
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
        """Delete ranking state permanently.
        
        Args:
            state_id: Ranking state UUID
            
        Returns:
            True if deletion successful
            
        Raises:
            ValueError: If state not found or deletion fails
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
        """Delete all ranking states for user.
        
        Useful for user cleanup or reset operations.
        
        Args:
            user_id: User unique identifier
            
        Returns:
            Number of states deleted
            
        Raises:
            ValueError: If deletion fails
        """
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
        """Retrieve ranking states showing drift signals.
        
        Identifies profiles requiring attention based on consecutive patterns.
        
        Args:
            user_id: User unique identifier
            top_threshold: Minimum consecutive top ranks to flag (default 3)
            drop_threshold: Minimum consecutive drops to flag (default 3)
            
        Returns:
            List of UserProfileRankingState objects with drift signals
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
        """Reset drift detection counters.
        
        Used after manual intervention or profile adjustment.
        
        Args:
            state_id: Ranking state UUID
            
        Returns:
            Updated UserProfileRankingState object
            
        Raises:
            ValueError: If state not found or reset fails
        """
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