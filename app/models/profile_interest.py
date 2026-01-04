"""Profile-Interest association model.

Defines many-to-many relationship between profiles and interest areas with weighting.
"""

from sqlalchemy import Column, String, Integer, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class ProfileInterest(Base):
    """Profile-Interest association entity.
    
    Links profiles to interest areas with configurable weights.
    Represents which interest areas are characteristic of each profile
    and their relative importance in profile matching.
    
    Attributes:
        profile_id: Foreign key reference to Profile
        interest_id: Foreign key reference to InterestArea
        weight: Relative importance of this interest (0.00 to 1.00)
        profile: Bidirectional relationship to Profile entity
        interest: Bidirectional relationship to InterestArea entity
    """
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
