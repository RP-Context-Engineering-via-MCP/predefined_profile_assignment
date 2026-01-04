"""Profile-Intent association model.

Defines many-to-many relationship between profiles and intents with weighting.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import relationship
from app.core.database import Base


class ProfileIntent(Base):
    """Profile-Intent association entity.
    
    Links profiles to intents with configurable weights and primary flags.
    Represents which intents are characteristic of each profile and their
    relative importance in profile identification.
    
    Attributes:
        profile_id: Foreign key reference to Profile
        intent_id: Foreign key reference to Intent
        is_primary: Flag indicating primary intent for the profile
        weight: Relative importance of this intent (0.00 to 1.00)
        profile: Bidirectional relationship to Profile entity
        intent: Bidirectional relationship to Intent entity
    """
    __tablename__ = "profile_intent"

    profile_id = Column(
        String(10),
        ForeignKey("profile.profile_id", ondelete="CASCADE"),
        primary_key=True
    )
    intent_id = Column(
        Integer,
        ForeignKey("intent.intent_id", ondelete="CASCADE"),
        primary_key=True
    )
    is_primary = Column(Boolean, default=False)
    weight = Column(Numeric(3, 2), default=1.0)

    profile = relationship("Profile", back_populates="intents")
    intent = relationship("Intent")
