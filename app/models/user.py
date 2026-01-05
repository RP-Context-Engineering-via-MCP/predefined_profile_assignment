"""User domain model.

Defines the User entity with authentication, profile assignment, and account management.
Supports both local authentication and OAuth providers (Google, GitHub).
"""

from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
from datetime import datetime


class UserStatus(str, enum.Enum):
    """Enumeration of possible user account states.
    
    Attributes:
        ACTIVE: User account is active and accessible
        SUSPENDED: User account is temporarily suspended
        DELETED: User account is marked for deletion
    """
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class UserProfileMode(str, enum.Enum):
    """Enumeration of user profile assignment modes.
    
    Attributes:
        COLD_START: Initial phase with limited behavioral data
        HYBRID: Uses both predefined and dynamic profiles
        DYNAMIC_ONLY: Uses only dynamically generated profiles
        DRIFT_FALLBACK: Fallback mode when behavior drift detected
    """
    COLD_START = "COLD_START"
    HYBRID = "HYBRID"
    DYNAMIC_ONLY = "DYNAMIC_ONLY"
    DRIFT_FALLBACK = "DRIFT_FALLBACK"


class User(Base):
    """User entity representing system users.
    
    Stores user authentication credentials, profile information, and profile
    assignment state. Supports both local authentication and OAuth providers.
    
    Attributes:
        user_id: Unique identifier (UUID format)
        username: Unique username for authentication
        email: User email address (unique)
        password_hash: Bcrypt hashed password (null for OAuth users)
    """
    __tablename__ = "user"

    user_id = Column(String(36), primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    
    name = Column(String(255), nullable=True)
    picture = Column(String(500), nullable=True)
    
    provider = Column(String(50), nullable=True, index=True)
    provider_id = Column(String(255), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_active_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)

    status = Column(
        Enum(UserStatus),
        default=UserStatus.ACTIVE,
        nullable=False,
        index=True
    )

    predefined_profile_id = Column(String(24), nullable=True, index=True)
    dynamic_profile_id = Column(String(24), nullable=True, index=True)

    profile_mode = Column(
        Enum(UserProfileMode),
        default=UserProfileMode.COLD_START,
        nullable=False,
        index=True
    )

    dynamic_profile_confidence = Column(String(50), default="0.0", nullable=False)
    dynamic_profile_ready = Column(String(5), default="false", nullable=False)

    fallback_profile_id = Column(String(24), nullable=True)
    fallback_reason = Column(String(500), nullable=True)
    fallback_activated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    domain_states = relationship("UserDomainState", back_populates="user", cascade="all, delete")

    def __repr__(self):
        """Return string representation of User instance."""
        return f"<User(user_id={self.user_id}, username={self.username}, email={self.email}, status={self.status}, profile_mode={self.profile_mode})>"