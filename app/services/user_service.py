# app/services/user_service.py

from sqlalchemy.orm import Session
from app.repositories.user_repo import UserRepository
from app.schemas.user_dto import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserListResponse,
    UserLoginRequest
)
import bcrypt
from typing import Optional, Tuple, List
from app.models.user import User


class UserService:
    """Service layer for user business logic"""

    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        # Encode password to bytes and truncate to 72 bytes (bcrypt limit)
        password_bytes = password.encode('utf-8')[:72]
        # Generate salt and hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        # Return as string
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hash
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against
            
        Returns:
            bool: True if password matches, False otherwise
        """
        # Encode both passwords to bytes
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        # Verify
        return bcrypt.checkpw(password_bytes, hashed_bytes)

    def create_user(self, user_data: UserCreateRequest) -> User:
        """
        Create a new user with hashed password
        
        Args:
            user_data: User creation data
            
        Returns:
            User: Created user object
            
        Raises:
            ValueError: If username or email already exists
        """
        # Hash the password
        password_hash = self.hash_password(user_data.password)
        
        # Create user
        user = self.repo.create_user(
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash,
            predefined_profile_id=user_data.predefined_profile_id,
            dynamic_profile_id=user_data.dynamic_profile_id,
            profile_mode=user_data.profile_mode,
            dynamic_profile_confidence=user_data.dynamic_profile_confidence or 0.0,
            dynamic_profile_ready=user_data.dynamic_profile_ready or False
        )
        
        return user

    def authenticate_user(self, login_data: UserLoginRequest) -> Optional[User]:
        """
        Authenticate a user
        
        Args:
            login_data: Login credentials
            
        Returns:
            User if authentication successful, None otherwise
        """
        user = self.repo.get_user_by_username(login_data.username)
        
        if not user:
            return None
        
        if not self.verify_password(login_data.password, user.password_hash):
            return None
        
        # Check if user is active
        if user.status != "active":
            return None
        
        return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.repo.get_user_by_id(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.repo.get_user_by_username(username)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.repo.get_user_by_email(email)

    def list_users(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[User], int]:
        """
        List users with filtering and pagination
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by status
            search: Search by username or email
            
        Returns:
            Tuple of (users list, total count)
        """
        if search:
            return self.repo.search_users(search, skip=skip, limit=limit)
        elif status:
            return self.repo.get_users_by_status(status, skip=skip, limit=limit)
        else:
            return self.repo.get_all_users(skip=skip, limit=limit)

    def update_user(self, user_id: str, user_data: UserUpdateRequest) -> User:
        """
        Update user
        
        Args:
            user_id: User ID to update
            user_data: Updated user data
            
        Returns:
            User: Updated user object
            
        Raises:
            ValueError: If user not found or validation fails
        """
        # Filter out None values
        update_dict = {k: v for k, v in user_data.dict().items() if v is not None}
        
        if not update_dict:
            raise ValueError("No fields to update")
        
        # Hash password if provided
        if "password" in update_dict:
            update_dict["password_hash"] = self.hash_password(update_dict.pop("password"))
        
        return self.repo.update_user(user_id, **update_dict)

    def delete_user(self, user_id: str, hard_delete: bool = False) -> bool:
        """
        Delete user
        
        Args:
            user_id: User ID to delete
            hard_delete: Whether to permanently delete
            
        Returns:
            bool: True if successful
        """
        return self.repo.delete_user(user_id, hard_delete=hard_delete)

    def activate_fallback_profile(
        self, 
        user_id: str, 
        fallback_profile_id: str, 
        reason: str
    ) -> User:
        """
        Activate fallback profile for drift handling
        
        Args:
            user_id: User ID
            fallback_profile_id: Profile ID to fallback to
            reason: Reason for fallback
            
        Returns:
            User: Updated user object
        """
        return self.repo.activate_fallback_profile(user_id, fallback_profile_id, reason)

    def deactivate_fallback_profile(self, user_id: str) -> User:
        """
        Deactivate fallback profile
        
        Args:
            user_id: User ID
            
        Returns:
            User: Updated user object
        """
        return self.repo.deactivate_fallback_profile(user_id)

    def change_password(
        self, 
        user_id: str, 
        old_password: str, 
        new_password: str
    ) -> User:
        """
        Change user password
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
            
        Returns:
            User: Updated user object
            
        Raises:
            ValueError: If old password is incorrect
        """
        user = self.repo.get_user_by_id(user_id)
        
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        
        # Verify old password
        if not self.verify_password(old_password, user.password_hash):
            raise ValueError("Incorrect current password")
        
        # Update password
        new_password_hash = self.hash_password(new_password)
        return self.repo.update_user(user_id, password_hash=new_password_hash)

    def suspend_user(self, user_id: str, reason: Optional[str] = None) -> User:
        """
        Suspend a user account
        
        Args:
            user_id: User ID
            reason: Reason for suspension
            
        Returns:
            User: Updated user object
        """
        update_data = {"status": "suspended"}
        if reason:
            update_data["fallback_reason"] = f"Suspended: {reason}"
        
        return self.repo.update_user(user_id, **update_data)

    def activate_user(self, user_id: str) -> User:
        """
        Activate a suspended user account
        
        Args:
            user_id: User ID
            
        Returns:
            User: Updated user object
        """
        return self.repo.update_user(user_id, status="active")