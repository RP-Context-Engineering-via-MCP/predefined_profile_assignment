"""Profile domain model.

Defines predefined user profiles with associated behavioral characteristics,
intents, interests, and interaction patterns.
"""

from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Profile(Base):
    """Predefined user profile entity.
    
    Represents a predefined behavioral profile with associated intents,
    interests, behavior levels, and interaction signals used for user
    classification and behavior prediction.
    
    Attributes:
        profile_id: Unique profile identifier (e.g., 'P1', 'P2')
        profile_name: Human-readable profile name
        description: Detailed profile description
        created_at: Profile creation timestamp
        intents: Related intent associations with weights
        interests: Related interest associations with weights
        behavior_levels: Associated behavioral complexity levels
        behavior_signals: Associated interaction style signals
    """
    __tablename__ = "profile"

    profile_id = Column(String(10), primary_key=True, index=True)
    profile_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    intents = relationship("ProfileIntent", back_populates="profile", cascade="all, delete")
    interests = relationship("ProfileInterest", back_populates="profile", cascade="all, delete")
    behavior_levels = relationship("ProfileBehaviorLevel", back_populates="profile", cascade="all, delete")
    behavior_signals = relationship("ProfileBehaviorSignal", back_populates="profile", cascade="all, delete")
    output_preferences = relationship("ProfileOutputPreference", back_populates="profile", cascade="all, delete")
    tones = relationship("ProfileTone", back_populates="profile", cascade="all, delete")
