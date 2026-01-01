# app/models/profile_trait.py

from sqlalchemy import Column, String, Integer, Numeric, ForeignKey
from app.core.database import Base


class ProfileTrait(Base):
    __tablename__ = "profile_trait"

    profile_id = Column(
        String(10),
        ForeignKey("profile.profile_id", ondelete="CASCADE"),
        primary_key=True
    )
    trait_id = Column(
        Integer,
        ForeignKey("trait.trait_id", ondelete="CASCADE"),
        primary_key=True
    )
    weight = Column(Numeric(3, 2), default=1.0)
