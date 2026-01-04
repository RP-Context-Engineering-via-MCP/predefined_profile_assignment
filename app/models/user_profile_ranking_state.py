"""User profile ranking state model.

Tracks temporal evolution of profile-user matching scores with aggregated
statistics and behavioral drift detection signals.
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, UniqueConstraint, Index
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime


class UserProfileRankingState(Base):
    """User-profile ranking state entity.
    
    Maintains aggregated scoring statistics and temporal patterns for each
    user-profile combination. Enables tracking of behavioral consistency,
    drift detection, and profile assignment confidence over time.
    
    Attributes:
        id: Unique identifier (UUID format)
        user_id: Foreign key reference to User entity
        profile_id: Foreign key reference to Profile entity
        cumulative_score: Sum of all historical matching scores
        average_score: Mean matching score across all observations
        max_score: Highest matching score ever recorded
        observation_count: Total number of scoring observations
        last_rank: Most recent ranking position (1 = top match)
        consecutive_top_count: Count of consecutive top rankings
        consecutive_drop_count: Count of consecutive rank drops
        updated_at: Last update timestamp (auto-managed)
    """
    __tablename__ = "user_profile_ranking_state"

    id = Column(String(36), primary_key=True, index=True)

    user_id = Column(String(36), nullable=False, index=True)
    profile_id = Column(String(24), nullable=False, index=True)

    cumulative_score = Column(Float, nullable=False, default=0.0)
    average_score = Column(Float, nullable=False, default=0.0)
    max_score = Column(Float, nullable=False, default=0.0)

    observation_count = Column(Integer, nullable=False, default=0)
    last_rank = Column(Integer, nullable=False, default=0)

    consecutive_top_count = Column(Integer, nullable=False, default=0)
    consecutive_drop_count = Column(Integer, nullable=False, default=0)

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint('user_id', 'profile_id', name='uix_user_profile'),
        Index('idx_user_profile', 'user_id', 'profile_id'),
        Index('idx_user_id', 'user_id'),
        Index('idx_profile_id', 'profile_id'),
        Index('idx_last_rank', 'last_rank'),
        Index('idx_updated_at', 'updated_at'),
    )

    def __repr__(self):
        """Return string representation of UserProfileRankingState instance."""
        return (
            f"<UserProfileRankingState("
            f"id={self.id}, "
            f"user_id={self.user_id}, "
            f"profile_id={self.profile_id}, "
            f"avg_score={self.average_score:.2f}, "
            f"rank={self.last_rank}, "
            f"observations={self.observation_count}"
            f")>"
        )

    def to_dict(self):
        """Convert model instance to dictionary representation.
        
        Returns:
            dict: Dictionary containing all model attributes with serialized values.
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "profile_id": self.profile_id,
            "cumulative_score": self.cumulative_score,
            "average_score": self.average_score,
            "max_score": self.max_score,
            "observation_count": self.observation_count,
            "last_rank": self.last_rank,
            "consecutive_top_count": self.consecutive_top_count,
            "consecutive_drop_count": self.consecutive_drop_count,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }