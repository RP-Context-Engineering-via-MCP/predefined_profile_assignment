"""Profile-Tone association model.

Defines many-to-many relationship between profiles and interaction tones with weighting.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.core.database import Base


class ProfileTone(Base):
    """Profile-Tone association entity.
    
    Links profiles to interaction tones with configurable weights.
    Represents which tones are characteristic of each profile
    and their relative importance.
    
    Attributes:
        profile_id: Foreign key reference to Profile
        tone_id: Foreign key reference to InteractionTone
        weight: Relative importance of this tone (0.0 to 1.0)
        profile: Bidirectional relationship to Profile entity
        tone: Bidirectional relationship to InteractionTone entity
    """
    __tablename__ = "profile_tone"

    profile_id = Column(
        String(10),
        ForeignKey("profile.profile_id", ondelete="CASCADE"),
        primary_key=True
    )
    tone_id = Column(
        Integer,
        ForeignKey("interaction_tone.tone_id", ondelete="CASCADE"),
        primary_key=True
    )
    weight = Column(Float, default=1.0)

    # Relationships
    profile = relationship(
        "Profile",
        back_populates="tones"
    )
    tone = relationship(
        "InteractionTone"
    )
