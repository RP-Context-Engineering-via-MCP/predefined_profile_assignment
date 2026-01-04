# app/models/user.py

from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
from datetime import datetime


class UserStatus(str, enum.Enum):
    """User status enumeration"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class UserProfileMode(str, enum.Enum):
    """User profile mode enumeration"""
    COLD_START = "COLD_START"
    HYBRID = "HYBRID"
    DYNAMIC_ONLY = "DYNAMIC_ONLY"
    DRIFT_FALLBACK = "DRIFT_FALLBACK"


class User(Base):
    __tablename__ = "user"

    # Primary identification
    user_id = Column(String(36), primary_key=True, index=True)  # UUID string (36 chars)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Store hashed password (nullable for OAuth users)
    
    # User profile info
    name = Column(String(255), nullable=True)  # Full name (from OAuth or user input)
    picture = Column(String(500), nullable=True)  # Profile picture URL
    
    # OAuth fields
    provider = Column(String(50), nullable=True, index=True)  # 'google', 'github', 'local', etc.
    provider_id = Column(String(255), nullable=True, index=True)  # OAuth provider's user ID

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_active_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)  # Track last login time

    # Account status
    status = Column(
        Enum(UserStatus),
        default=UserStatus.ACTIVE,
        nullable=False,
        index=True
    )

    # Profile references (stored as strings for ObjectId references)
    predefined_profile_id = Column(String(24), nullable=True, index=True)
    dynamic_profile_id = Column(String(24), nullable=True, index=True)

    # Profile control state
    profile_mode = Column(
        Enum(UserProfileMode),
        default=UserProfileMode.COLD_START,
        nullable=False,
        index=True
    )

    # Cold-start & stability
    dynamic_profile_confidence = Column(String(50), default="0.0", nullable=False)  # Store as string for precision
    dynamic_profile_ready = Column(String(5), default="false", nullable=False)  # Store as string ("true"/"false")

    # Drift handling
    fallback_profile_id = Column(String(24), nullable=True)
    fallback_reason = Column(String(500), nullable=True)
    fallback_activated_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username}, email={self.email}, status={self.status}, profile_mode={self.profile_mode})>"