"""User Domain State model.

Tracks per-user, per-domain expertise with dynamic updates.
"""

from sqlalchemy import Column, Integer, ForeignKey, Float, DateTime, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserDomainState(Base):
    """User domain state entity.
    
    Tracks user expertise level in specific interest domains.
    Updated dynamically based on user interactions and behaviors.
    
    Attributes:
        user_id: Foreign key reference to User (UUID type)
        interest_id: Foreign key reference to InterestArea
        expertise_level_id: Foreign key reference to DomainExpertiseLevel
        confidence_score: Confidence in the expertise assessment (0.0 to 1.0)
        last_updated: Timestamp of last update
        user: Bidirectional relationship to User entity
        interest: Bidirectional relationship to InterestArea entity
        expertise_level: Bidirectional relationship to DomainExpertiseLevel entity
    """
    __tablename__ = "user_domain_state"

    user_id = Column(
        String(36),
        ForeignKey("user.user_id", ondelete="CASCADE"),
        primary_key=True
    )
    interest_id = Column(
        Integer,
        ForeignKey("interest_area.interest_id", ondelete="CASCADE"),
        primary_key=True
    )
    expertise_level_id = Column(
        Integer,
        ForeignKey("domain_expertise_level.expertise_level_id", ondelete="CASCADE"),
        nullable=False
    )
    confidence_score = Column(Float, default=0.0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship(
        "User",
        back_populates="domain_states"
    )
    interest = relationship(
        "InterestArea"
    )
    expertise_level = relationship(
        "DomainExpertiseLevel"
    )
