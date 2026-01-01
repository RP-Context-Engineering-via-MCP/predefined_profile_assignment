# app/repositories/user_repo.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user import User, UserStatus, UserProfileMode
from datetime import datetime
import uuid


class UserRepository:
    """Repository for User model CRUD operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_user(self, username: str, email: str, password_hash: str,
                   predefined_profile_id: str = None, 
                   dynamic_profile_id: str = None, profile_mode: str = "COLD_START",
                   dynamic_profile_confidence: float = 0.0, 
                   dynamic_profile_ready: bool = False) -> User:
        """
        Create a new user
        
        Args:
            username: Username
            email: User email address
            password_hash: Hashed password
            predefined_profile_id: Reference to predefined profile
            dynamic_profile_id: Reference to dynamic profile
            profile_mode: Profile mode (COLD_START, HYBRID, DYNAMIC_ONLY, DRIFT_FALLBACK)
            dynamic_profile_confidence: Confidence score for dynamic profile
            dynamic_profile_ready: Whether dynamic profile is ready
            
        Returns:
            User: Created user object
            
        Raises:
            IntegrityError: If username or email already exists
        """
        try:
            user = User(
                user_id=str(uuid.uuid4()),
                username=username,
                email=email,
                password_hash=password_hash,
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
        """Get user by user_id"""
        return self.db.query(User).filter(User.user_id == user_id).first()

    def get_user_by_username(self, username: str) -> User:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, email: str) -> User:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_all_users(self, skip: int = 0, limit: int = 100) -> tuple[list[User], int]:
        """
        Get all users with pagination
        
        Returns:
            Tuple of (users list, total count)
        """
        query = self.db.query(User).filter(User.status != UserStatus.DELETED)
        total = query.count()
        users = query.offset(skip).limit(limit).all()
        return users, total

    def get_users_by_status(self, status: str, skip: int = 0, limit: int = 100) -> tuple[list[User], int]:
        """Get users filtered by status"""
        query = self.db.query(User).filter(User.status == UserStatus(status))
        total = query.count()
        users = query.offset(skip).limit(limit).all()
        return users, total

    def update_user(self, user_id: str, **kwargs) -> User:
        """
        Update user fields
        
        Args:
            user_id: User ID to update
            **kwargs: Fields to update
            
        Returns:
            User: Updated user object
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        # Map and validate incoming data
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
        """
        Delete a user (soft or hard delete)
        
        Args:
            user_id: User ID to delete
            hard_delete: If True, permanently delete; if False, mark as deleted
            
        Returns:
            bool: True if deletion was successful
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
        """
        Activate fallback profile for a user (drift handling)
        
        Args:
            user_id: User ID
            fallback_profile_id: Profile ID to fallback to
            reason: Reason for fallback
            
        Returns:
            User: Updated user object
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
        """
        Deactivate fallback profile for a user
        
        Args:
            user_id: User ID
            
        Returns:
            User: Updated user object
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
        """Search users by username or email"""
        db_query = self.db.query(User).filter(
            (User.username.ilike(f"%{query}%") | User.email.ilike(f"%{query}%")),
            User.status != UserStatus.DELETED
        )
        total = db_query.count()
        users = db_query.offset(skip).limit(limit).all()
        return users, total