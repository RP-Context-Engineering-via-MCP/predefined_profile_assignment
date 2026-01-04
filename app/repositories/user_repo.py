"""User repository.

Provides data access layer for User entity CRUD operations,
including authentication, profile management, and drift handling.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user import User, UserStatus, UserProfileMode
from datetime import datetime
import uuid


class UserRepository:
    """User data access repository.
    
    Handles all database operations for User entities including creation,
    retrieval, updates, and deletion. Supports both traditional and OAuth
    authentication workflows.
    
    Attributes:
        db: SQLAlchemy database session
    """

    def __init__(self, db: Session):
        """Initialize repository with database session.
        
        Args:
            db: Active SQLAlchemy session
        """
        self.db = db

    def create_user(self, username: str, email: str, password_hash: str = None,
                   predefined_profile_id: str = None, 
                   dynamic_profile_id: str = None, profile_mode: str = "COLD_START",
                   dynamic_profile_confidence: float = 0.0, 
                   dynamic_profile_ready: bool = False,
                   name: str = None,
                   picture: str = None,
                   provider: str = None,
                   provider_id: str = None) -> User:
        """Create new user with validation.
        
        Supports both traditional (password-based) and OAuth authentication.
        Automatically generates UUID and sets initial status to ACTIVE.
        
        Args:
            username: Unique username (3-50 chars)
            email: Valid email address (unique)
            password_hash: Bcrypt password hash (None for OAuth users)
            predefined_profile_id: Initial profile assignment
            dynamic_profile_id: Dynamic profile reference
            profile_mode: Profile mode (COLD_START, HYBRID, DYNAMIC_ONLY, DRIFT_FALLBACK)
            dynamic_profile_confidence: Confidence score for dynamic profile (0.0-1.0)
            dynamic_profile_ready: Dynamic profile readiness flag
            name: User's full name (for OAuth)
            picture: Profile picture URL (for OAuth)
            provider: OAuth provider (google, github, etc.)
            provider_id: OAuth provider's unique user identifier
            
        Returns:
            Created and persisted User object
            
        Raises:
            ValueError: If username or email already exists, or constraint violation
        """
        try:
            user = User(
                user_id=str(uuid.uuid4()),
                username=username,
                email=email,
                password_hash=password_hash,
                name=name,
                picture=picture,
                provider=provider,
                provider_id=provider_id,
                predefined_profile_id=predefined_profile_id,
                dynamic_profile_id=dynamic_profile_id,
                profile_mode=UserProfileMode(profile_mode),
                dynamic_profile_confidence=str(dynamic_profile_confidence),
                dynamic_profile_ready="true" if dynamic_profile_ready else "false",
                status=UserStatus.ACTIVE
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError as e:
            self.db.rollback()
            if 'username' in str(e.orig):
                raise ValueError(f"Username '{username}' already exists")
            elif 'email' in str(e.orig):
                raise ValueError(f"Email '{email}' already exists")
            raise ValueError("User creation failed due to constraint violation")

    def get_user_by_id(self, user_id: str) -> User:
        """Retrieve user by unique identifier.
        
        Args:
            user_id: User UUID
            
        Returns:
            User object or None if not found
        """
        return self.db.query(User).filter(User.user_id == user_id).first()

    def get_user_by_username(self, username: str) -> User:
        """Retrieve user by username.
        
        Args:
            username: Unique username
            
        Returns:
            User object or None if not found
        """
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, email: str) -> User:
        """Retrieve user by email address.
        
        Args:
            email: User's email
            
        Returns:
            User object or None if not found
        """
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_provider(self, provider: str, provider_id: str) -> User:
        """Retrieve user by OAuth provider credentials.
        
        Args:
            provider: OAuth provider name (google, github, etc.)
            provider_id: Provider's unique user identifier
            
        Returns:
            User object or None if not found
        """
        return self.db.query(User).filter(
            User.provider == provider,
            User.provider_id == provider_id
        ).first()

    def update_last_login(self, user_id: str) -> User:
        """Update user's last login timestamp.
        
        Args:
            user_id: User UUID
            
        Returns:
            Updated User object or None if not found
        """
        user = self.get_user_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
        return user

    def get_all_users(self, skip: int = 0, limit: int = 100) -> tuple[list[User], int]:
        """Retrieve all active users with pagination.
        
        Excludes users with DELETED status.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum records to return
            
        Returns:
            Tuple of (user list, total count)
        """
        query = self.db.query(User).filter(User.status != UserStatus.DELETED)
        total = query.count()
        users = query.offset(skip).limit(limit).all()
        return users, total

    def get_users_by_status(self, status: str, skip: int = 0, limit: int = 100) -> tuple[list[User], int]:
        """Retrieve users filtered by account status.
        
        Args:
            status: Status filter (active, suspended, deleted)
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            Tuple of (user list, total count)
        """
        query = self.db.query(User).filter(User.status == UserStatus(status))
        total = query.count()
        users = query.offset(skip).limit(limit).all()
        return users, total

    def update_user(self, user_id: str, **kwargs) -> User:
        """Update user fields with validation.
        
        Supports partial updates with uniqueness checks for username and email.
        Automatically updates last_active_at timestamp.
        
        Args:
            user_id: User UUID to update
            **kwargs: Field-value pairs to update. Supported fields:
                username, email, password_hash, status, predefined_profile_id,
                dynamic_profile_id, profile_mode, dynamic_profile_confidence,
                dynamic_profile_ready, fallback_profile_id, fallback_reason,
                fallback_activated_at
            
        Returns:
            Updated User object
            
        Raises:
            ValueError: If user not found, username/email taken, or constraint violation
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        update_data = {}
        
        if "username" in kwargs and kwargs["username"]:
            # Check if username already exists (and is not the same user)
            existing = self.db.query(User).filter(
                User.username == kwargs["username"],
                User.user_id != user_id
            ).first()
            if existing:
                raise ValueError(f"Username '{kwargs['username']}' is already taken")
            update_data["username"] = kwargs["username"]

        if "email" in kwargs and kwargs["email"]:
            # Check if email already exists (and is not the same user)
            existing = self.db.query(User).filter(
                User.email == kwargs["email"],
                User.user_id != user_id
            ).first()
            if existing:
                raise ValueError(f"Email '{kwargs['email']}' is already in use")
            update_data["email"] = kwargs["email"]

        if "password_hash" in kwargs and kwargs["password_hash"]:
            update_data["password_hash"] = kwargs["password_hash"]

        if "status" in kwargs and kwargs["status"]:
            update_data["status"] = UserStatus(kwargs["status"])

        if "predefined_profile_id" in kwargs:
            update_data["predefined_profile_id"] = kwargs["predefined_profile_id"]

        if "dynamic_profile_id" in kwargs:
            update_data["dynamic_profile_id"] = kwargs["dynamic_profile_id"]

        if "profile_mode" in kwargs and kwargs["profile_mode"]:
            update_data["profile_mode"] = UserProfileMode(kwargs["profile_mode"])

        if "dynamic_profile_confidence" in kwargs and kwargs["dynamic_profile_confidence"] is not None:
            update_data["dynamic_profile_confidence"] = str(kwargs["dynamic_profile_confidence"])

        if "dynamic_profile_ready" in kwargs and kwargs["dynamic_profile_ready"] is not None:
            update_data["dynamic_profile_ready"] = "true" if kwargs["dynamic_profile_ready"] else "false"

        if "fallback_profile_id" in kwargs:
            update_data["fallback_profile_id"] = kwargs["fallback_profile_id"]

        if "fallback_reason" in kwargs:
            update_data["fallback_reason"] = kwargs["fallback_reason"]

        if "fallback_activated_at" in kwargs:
            update_data["fallback_activated_at"] = kwargs["fallback_activated_at"]

        # Update last_active_at
        update_data["last_active_at"] = datetime.utcnow()

        try:
            for key, value in update_data.items():
                setattr(user, key, value)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise ValueError("Failed to update user - constraint violation")

    def delete_user(self, user_id: str, hard_delete: bool = False) -> bool:
        """Delete user (soft or hard).
        
        Soft delete marks user as DELETED status (preserves data).
        Hard delete permanently removes from database.
        
        Args:
            user_id: User UUID to delete
            hard_delete: If True, permanent deletion; if False, soft delete
            
        Returns:
            True if deletion successful
            
        Raises:
            ValueError: If user not found or deletion fails
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        try:
            if hard_delete:
                self.db.delete(user)
            else:
                user.status = UserStatus.DELETED
                user.last_active_at = datetime.utcnow()
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to delete user: {str(e)}")

    def activate_fallback_profile(self, user_id: str, fallback_profile_id: str, 
                                 reason: str) -> User:
        """Activate drift fallback profile.
        
        Switches user to DRIFT_FALLBACK mode and records fallback details.
        Used when behavioral drift is detected.
        
        Args:
            user_id: User UUID
            fallback_profile_id: Profile to fall back to
            reason: Explanation for fallback activation
            
        Returns:
            Updated User object
            
        Raises:
            ValueError: If user not found or activation fails
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        user.fallback_profile_id = fallback_profile_id
        user.fallback_reason = reason
        user.fallback_activated_at = datetime.utcnow()
        user.profile_mode = UserProfileMode.DRIFT_FALLBACK
        user.last_active_at = datetime.utcnow()

        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to activate fallback profile: {str(e)}")

    def deactivate_fallback_profile(self, user_id: str) -> User:
        """Deactivate drift fallback profile.
        
        Clears fallback profile and switches to HYBRID mode.
        
        Args:
            user_id: User UUID
            
        Returns:
            Updated User object
            
        Raises:
            ValueError: If user not found or deactivation fails
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        user.fallback_profile_id = None
        user.fallback_reason = None
        user.fallback_activated_at = None
        user.profile_mode = UserProfileMode.HYBRID  # or appropriate mode
        user.last_active_at = datetime.utcnow()

        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to deactivate fallback profile: {str(e)}")

    def search_users(self, query: str, skip: int = 0, limit: int = 100) -> tuple[list[User], int]:
        """Search users by username or email.
        
        Case-insensitive partial matching on username and email fields.
        Excludes deleted users.
        
        Args:
            query: Search term to match
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            Tuple of (matching users, total count)
        """
        db_query = self.db.query(User).filter(
            (User.username.ilike(f"%{query}%") | User.email.ilike(f"%{query}%")),
            User.status != UserStatus.DELETED
        )
        total = db_query.count()
        users = db_query.offset(skip).limit(limit).all()
        return users, total