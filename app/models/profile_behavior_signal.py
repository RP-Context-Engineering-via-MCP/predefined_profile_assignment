# app/models/profile_behavior_signal.py

from sqlalchemy import Column, String, Integer, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.core.database import Base


class ProfileBehaviorSignal(Base):
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
