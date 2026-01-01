# app/models/profile_version.py

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base


class ProfileVersion(Base):
    __tablename__ = "profile_version"

    profile_id = Column(
        String(10),
        ForeignKey("profile.profile_id", ondelete="CASCADE"),
        primary_key=True
    )
    version = Column(Integer, primary_key=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
