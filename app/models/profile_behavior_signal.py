"""Profile-Behavior Signal association model.

Defines many-to-many relationship between profiles and interaction style signals.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.core.database import Base


class ProfileBehaviorSignal(Base):
    """Profile-Behavior Signal association entity.
    
    Links profiles to behavioral signals with configurable weights.
    Represents which interaction styles are characteristic of each profile
    and their relative importance in behavioral analysis.
    
    Attributes:
        profile_id: Foreign key reference to Profile
        signal_id: Foreign key reference to BehaviorSignal
        weight: Relative importance of this signal (0.00 to 1.00)
        profile: Bidirectional relationship to Profile entity
        signal: Bidirectional relationship to BehaviorSignal entity
    """
    __tablename__ = "profile_behavior_signal"

    profile_id = Column(
        String(10),
        ForeignKey("profile.profile_id", ondelete="CASCADE"),
        primary_key=True
    )
    signal_id = Column(
        Integer,
        ForeignKey("behavior_signal.signal_id", ondelete="CASCADE"),
        primary_key=True
    )
    weight = Column(Numeric(3, 2), default=1.0)

    profile = relationship("Profile", back_populates="behavior_signals")
    signal = relationship("BehaviorSignal")
