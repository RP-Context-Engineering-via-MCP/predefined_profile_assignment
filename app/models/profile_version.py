"""Profile version model.

Tracks different versions of profile configurations for versioning and rollback.
"""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base


class ProfileVersion(Base):
    """Profile version entity.
    
    Maintains version history for profile configurations.
    Enables tracking of profile changes and rollback to previous versions.
    
    Attributes:
        profile_id: Foreign key reference to Profile
        version: Version number (incremental)
        is_active: Flag indicating if this version is currently active
        created_at: Version creation timestamp
    """
    __tablename__ = "profile_version"

    profile_id = Column(
        String(10),
        ForeignKey("profile.profile_id", ondelete="CASCADE"),
        primary_key=True
    )
    version = Column(Integer, primary_key=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
