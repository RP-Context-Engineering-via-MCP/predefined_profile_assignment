# app/models/profile_intent.py

from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import relationship
from app.core.database import Base


class ProfileIntent(Base):
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
