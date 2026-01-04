"""Profile-Domain association model.

Defines many-to-many relationship between profiles and knowledge domains.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Numeric
from app.core.database import Base


class ProfileDomain(Base):
    """Profile-Domain association entity.
    
    Links profiles to knowledge or interest domains with configurable weights.
    Represents which domains are characteristic of each profile.
    
    Attributes:
        profile_id: Foreign key reference to Profile
        domain_id: Foreign key reference to Domain
        weight: Relative importance of this domain (0.00 to 1.00)
    """
    __tablename__ = "profile_domain"

    profile_id = Column(
        String(10),
        ForeignKey("profile.profile_id", ondelete="CASCADE"),
        primary_key=True
    )
    domain_id = Column(
        Integer,
        ForeignKey("domain.domain_id", ondelete="CASCADE"),
        primary_key=True
    )
    weight = Column(Numeric(3, 2), default=1.0)
