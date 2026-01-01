# app/models/profile_domain.py

from sqlalchemy import Column, String, Integer, ForeignKey, Numeric
from app.core.database import Base


class ProfileDomain(Base):
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
