"""User Domain State Repository.

Handles database operations for tracking user expertise levels across domains.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.user_domain_state import UserDomainState
from app.models.domain_expertise_level import DomainExpertiseLevel


class UserDomainStateRepository:
    """Repository for user domain state operations."""

    @staticmethod
    def get_user_domain_state(
        db: Session,
        user_id: str,
        interest_id: int
    ) -> Optional[UserDomainState]:
        """Get user's expertise state for a specific domain.
        
        Args:
            db: Database session
            user_id: User identifier
            interest_id: Interest area identifier
            
        Returns:
            UserDomainState if exists, None otherwise
        """
        return db.query(UserDomainState).filter(
            and_(
                UserDomainState.user_id == user_id,
                UserDomainState.interest_id == interest_id
            )
        ).first()

    @staticmethod
    def get_all_user_domain_states(
        db: Session,
        user_id: str
    ) -> List[UserDomainState]:
        """Get all domain expertise states for a user.
        
        Args:
            db: Database session
            user_id: User identifier
            
        Returns:
            List of UserDomainState records
        """
        return db.query(UserDomainState).filter(
            UserDomainState.user_id == user_id
        ).all()

    @staticmethod
    def upsert_user_domain_state(
        db: Session,
        user_id: str,
        interest_id: int,
        expertise_level_id: int,
        confidence_score: float
    ) -> UserDomainState:
        """Insert or update user domain state.
        
        Uses ON CONFLICT logic to handle existing records.
        
        Args:
            db: Database session
            user_id: User identifier
            interest_id: Interest area identifier
            expertise_level_id: New expertise level ID
            confidence_score: New confidence score (0.0 to 1.0)
            
        Returns:
            Updated or created UserDomainState
        """
        existing = UserDomainStateRepository.get_user_domain_state(
            db, user_id, interest_id
        )

        if existing:
            existing.expertise_level_id = expertise_level_id
            existing.confidence_score = confidence_score
            db.commit()
            db.refresh(existing)
            return existing
        else:
            new_state = UserDomainState(
                user_id=user_id,
                interest_id=interest_id,
                expertise_level_id=expertise_level_id,
                confidence_score=confidence_score
            )
            db.add(new_state)
            db.commit()
            db.refresh(new_state)
            return new_state

    @staticmethod
    def get_expertise_level_by_name(
        db: Session,
        level_name: str
    ) -> Optional[DomainExpertiseLevel]:
        """Get expertise level by name.
        
        Args:
            db: Database session
            level_name: Level name (e.g., 'BEGINNER', 'INTERMEDIATE', 'ADVANCED')
            
        Returns:
            DomainExpertiseLevel if exists, None otherwise
        """
        return db.query(DomainExpertiseLevel).filter(
            DomainExpertiseLevel.level_name == level_name
        ).first()

    @staticmethod
    def get_expertise_level_id_by_confidence(
        db: Session,
        confidence_score: float
    ) -> int:
        """Determine expertise level ID based on confidence score.
        
        Thresholds:
        - BEGINNER: 0.00 – 0.39
        - INTERMEDIATE: 0.40 – 0.74
        - ADVANCED: 0.75 – 1.00
        
        Args:
            db: Database session
            confidence_score: Confidence score (0.0 to 1.0)
            
        Returns:
            Expertise level ID
        """
        if confidence_score < 0.40:
            level_name = "BEGINNER"
        elif confidence_score < 0.75:
            level_name = "INTERMEDIATE"
        else:
            level_name = "ADVANCED"

        level = UserDomainStateRepository.get_expertise_level_by_name(db, level_name)
        return level.expertise_level_id if level else 1  # Default to BEGINNER

    @staticmethod
    def apply_decay_to_inactive_states(
        db: Session,
        days_threshold: int = 30,
        decay_factor: float = 0.98
    ) -> int:
        """Apply time-based decay to inactive domain states.
        
        Args:
            db: Database session
            days_threshold: Days of inactivity before decay applies
            decay_factor: Multiplier for confidence (e.g., 0.98 = 2% decay)
            
        Returns:
            Number of records updated
        """
        from sqlalchemy import func, text
        
        query = text("""
            UPDATE user_domain_state
            SET confidence_score = confidence_score * :decay_factor,
                last_updated = CURRENT_TIMESTAMP
            WHERE last_updated < CURRENT_TIMESTAMP - INTERVAL ':days days'
        """)
        
        result = db.execute(query, {
            "decay_factor": decay_factor,
            "days": days_threshold
        })
        db.commit()
        return result.rowcount

    @staticmethod
    def delete_user_domain_state(
        db: Session,
        user_id: str,
        interest_id: int
    ) -> bool:
        """Delete a user domain state record.
        
        Args:
            db: Database session
            user_id: User identifier
            interest_id: Interest area identifier
            
        Returns:
            True if deleted, False if not found
        """
        state = UserDomainStateRepository.get_user_domain_state(db, user_id, interest_id)
        if state:
            db.delete(state)
            db.commit()
            return True
        return False
