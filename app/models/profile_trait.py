"""Profile-Trait association model.

Defines many-to-many relationship between profiles and personality traits.
"""

from sqlalchemy import Column, String, Integer, Numeric, ForeignKey
from app.core.database import Base


class ProfileTrait(Base):
    """Profile-Trait association entity.
    
    Links profiles to personality or behavioral traits with configurable weights.
    Represents which traits are characteristic of each profile.
    
    Attributes:
        profile_id: Foreign key reference to Profile
        trait_id: Foreign key reference to Trait
        weight: Relative importance of this trait (0.00 to 1.00)
    """
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
