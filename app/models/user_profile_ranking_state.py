# app/models/user_profile_ranking_state.py

from sqlalchemy import Column, String, Float, Integer, DateTime, UniqueConstraint, Index
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime


class UserProfileRankingState(Base):
    """
    Model for tracking user-profile ranking states over time.
    Stores aggregated scores, temporal statistics, and drift signals.
    """
    __tablename__ = "user_profile_ranking_state"

    # Primary key
    id = Column(String(36), primary_key=True, index=True)  # UUID string

    # Foreign keys (stored as strings)
    user_id = Column(String(36), nullable=False, index=True)  # References user.user_id
    profile_id = Column(String(24), nullable=False, index=True)  # References profile ObjectId

    # Aggregated scores
    cumulative_score = Column(Float, nullable=False, default=0.0)
    average_score = Column(Float, nullable=False, default=0.0)
    max_score = Column(Float, nullable=False, default=0.0)

    # Temporal stats
    observation_count = Column(Integer, nullable=False, default=0)
    last_rank = Column(Integer, nullable=False, default=0)

    # Drift signals
    consecutive_top_count = Column(Integer, nullable=False, default=0)
    consecutive_drop_count = Column(Integer, nullable=False, default=0)

    # Timestamp
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'profile_id', name='uix_user_profile'),
        Index('idx_user_profile', 'user_id', 'profile_id'),
        Index('idx_user_id', 'user_id'),
        Index('idx_profile_id', 'profile_id'),
        Index('idx_last_rank', 'last_rank'),
        Index('idx_updated_at', 'updated_at'),
    )

    def __repr__(self):
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
        """Convert model to dictionary"""
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