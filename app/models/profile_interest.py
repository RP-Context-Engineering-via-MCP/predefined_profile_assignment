# app/models/profile_interest.py

from sqlalchemy import Column, String, Integer, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class ProfileInterest(Base):
    __tablename__ = "profile_interest"

    profile_id = Column(
        String(10),
        ForeignKey("profile.profile_id", ondelete="CASCADE"),
        primary_key=True
    )
    interest_id = Column(
        Integer,
        ForeignKey("interest_area.interest_id", ondelete="CASCADE"),
        primary_key=True
    )
    weight = Column(Numeric(3, 2), default=1.0)

    profile = relationship("Profile", back_populates="interests")
    interest = relationship("InterestArea")
