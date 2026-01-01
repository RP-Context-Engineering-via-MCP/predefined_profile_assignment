# app/models/profile_behavior_level.py

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class ProfileBehaviorLevel(Base):
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
