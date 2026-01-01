# app/models/profile.py

from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Profile(Base):
    __tablename__ = "profile"

    profile_id = Column(String(10), primary_key=True, index=True)
    profile_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # 🔗 Relationships
    intents = relationship("ProfileIntent", back_populates="profile", cascade="all, delete")
    interests = relationship("ProfileInterest", back_populates="profile", cascade="all, delete")
    behavior_levels = relationship("ProfileBehaviorLevel", back_populates="profile", cascade="all, delete")
    behavior_signals = relationship("ProfileBehaviorSignal", back_populates="profile", cascade="all, delete")
