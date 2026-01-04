"""Profile-Behavior Level association model.

Defines many-to-many relationship between profiles and behavior complexity levels.
"""

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class ProfileBehaviorLevel(Base):
    """Profile-Behavior Level association entity.
    
    Links profiles to behavioral complexity levels.
    Represents which complexity levels are characteristic of each profile.
    
    Attributes:
        profile_id: Foreign key reference to Profile
        behavior_level_id: Foreign key reference to BehaviorLevel
        profile: Bidirectional relationship to Profile entity
        level: Bidirectional relationship to BehaviorLevel entity
    """
    __tablename__ = "profile_behavior_level"

    profile_id = Column(
        String(10),
        ForeignKey("profile.profile_id", ondelete="CASCADE"),
        primary_key=True
    )
    behavior_level_id = Column(
        Integer,
        ForeignKey("behavior_level.behavior_level_id", ondelete="CASCADE"),
        primary_key=True
    )

    profile = relationship("Profile", back_populates="behavior_levels")
    level = relationship("BehaviorLevel")
