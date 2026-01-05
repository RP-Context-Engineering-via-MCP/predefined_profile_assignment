"""Profile-Output Preference association model.

Defines many-to-many relationship between profiles and output preferences with weighting.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.core.database import Base


class ProfileOutputPreference(Base):
    """Profile-Output Preference association entity.
    
    Links profiles to output preferences with configurable weights.
    Represents which output formats are characteristic of each profile
    and their relative importance.
    
    Attributes:
        profile_id: Foreign key reference to Profile
        output_pref_id: Foreign key reference to OutputPreference
        weight: Relative importance of this preference (0.0 to 1.0)
        profile: Bidirectional relationship to Profile entity
        output_preference: Bidirectional relationship to OutputPreference entity
    """
    __tablename__ = "profile_output_preference"

    profile_id = Column(
        String(10),
        ForeignKey("profile.profile_id", ondelete="CASCADE"),
        primary_key=True
    )
    output_pref_id = Column(
        Integer,
        ForeignKey("output_preference.output_pref_id", ondelete="CASCADE"),
        primary_key=True
    )
    weight = Column(Float, default=1.0)

    # Relationships
    profile = relationship(
        "Profile",
        back_populates="output_preferences"
    )
    output_preference = relationship(
        "OutputPreference"
    )
