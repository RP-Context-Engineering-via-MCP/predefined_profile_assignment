"User business logic service.

Provides high-level user operations including authentication,
registration, OAuth handling, and profile management."

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
    """User business logic service.
    
    Orchestrates user operations including password management,
    authentication, OAuth integration, and account lifecycle.
    
    Attributes:
        repo: User repository
    """

    def __init__(self, db: Session):
        """Initialize service with database session.
        
        Args:
            db: Active SQLAlchemy session
        """
        self.repo = UserRepository(db)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Bcrypt hashed password string
        """
        password_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against bcrypt hash.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Bcrypt hash to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)

    def create_user(self, user_data: UserCreateRequest) -> User:
        """Create new user with hashed password.
        
        Args:
            user_data: User creation request
            
        Returns:
            Created User object
            
        Raises:
            ValueError: If username or email already exists
        """
        password_hash = self.hash_password(user_data.password)
        
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
        """Authenticate user with credentials.
        
        Args:
            login_data: Login credentials (username and password)
            
        Returns:
            User object if authentication successful, None otherwise
        """
        user = self.repo.get_user_by_username(login_data.username)
        
        if not user:
            return None
        
        if not self.verify_password(login_data.password, user.password_hash):
            return None
        
        if user.status != "active":
            return None
        
        return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve user by unique identifier.
        
        Args:
            user_id: User UUID
            
        Returns:
            User object or None
        """
        return self.repo.get_user_by_id(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieve user by username.
        
        Args:
            username: Unique username
            
        Returns:
            User object or None
        """
        return self.repo.get_user_by_username(username)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieve user by email address.
        
        Args:
            email: User's email
            
        Returns:
            User object or None
        """
        return self.repo.get_user_by_email(email)

    def oauth_login_or_register(self, email: str, name: str, provider: str, provider_id: str, picture: Optional[str] = None) -> Tuple[User, bool]:
        """Handle OAuth login or registration.
        
        Checks if user exists by email or provider credentials:
        - If exists: returns existing user (updates OAuth info)
        - If not exists: creates new OAuth user
        
        Args:
            email: User's email from OAuth provider
            name: User's full name from OAuth provider
            provider: OAuth provider name (google, github, etc.)
            provider_id: OAuth provider's unique user ID
            picture: Profile picture URL (optional)
            
        Returns:
            Tuple of (User object, is_new_user flag)
        """
        existing_user = self.repo.get_user_by_provider(provider, provider_id)
        
        if existing_user:
            self.repo.update_last_login(existing_user.user_id)
            return existing_user, False
        
        existing_user = self.repo.get_user_by_email(email)
        
        if existing_user:
            existing_user.provider = provider
            existing_user.provider_id = provider_id
            if picture:
                existing_user.picture = picture
            if name and not existing_user.name:
                existing_user.name = name
            self.repo.db.commit()
            self.repo.db.refresh(existing_user)
            self.repo.update_last_login(existing_user.user_id)
            return existing_user, False
        
        username = email.split('@')[0]
        
        base_username = username
        counter = 1
        while self.repo.get_user_by_username(username):
            username = f"{base_username}{counter}"
            counter += 1
        
        user = self.repo.create_user(
            username=username,
            email=email,
            password_hash=None,
            name=name,
            picture=picture,
            provider=provider,
            provider_id=provider_id
        )
        
        self.repo.update_last_login(user.user_id)
        
        return user, True

    def list_users(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[User], int]:
        """List users with filtering and pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            status: Filter by status (active, suspended, deleted)
            search: Search by username or email
            
        Returns:
            Tuple of (user list, total count)
        """
        if search:
            return self.repo.search_users(search, skip=skip, limit=limit)
        elif status:
            return self.repo.get_users_by_status(status, skip=skip, limit=limit)
        else:
            return self.repo.get_all_users(skip=skip, limit=limit)

    def update_user(self, user_id: str, user_data: UserUpdateRequest) -> User:
        """Update user with partial data.
        
        Args:
            user_id: User UUID to update
            user_data: Update request with new values
            
        Returns:
            Updated User object
            
        Raises:
            ValueError: If no fields to update or user not found
        """
        update_dict = {k: v for k, v in user_data.dict().items() if v is not None}
        
        if not update_dict:
            raise ValueError("No fields to update")
        
        if "password" in update_dict:
            update_dict["password_hash"] = self.hash_password(update_dict.pop("password"))
        
        return self.repo.update_user(user_id, **update_dict)

    def delete_user(self, user_id: str, hard_delete: bool = False) -> bool:
        """Delete user (soft or hard).
        
        Args:
            user_id: User UUID to delete
            hard_delete: If True, permanent deletion; if False, soft delete
            
        Returns:
            True if successful
        """
        return self.repo.delete_user(user_id, hard_delete=hard_delete)

    def activate_fallback_profile(
        self, 
        user_id: str, 
        fallback_profile_id: str, 
        reason: str
    ) -> User:
        """Activate fallback profile for drift handling.
        
        Args:
            user_id: User UUID
            fallback_profile_id: Profile to fall back to
            reason: Explanation for fallback activation
            
        Returns:
            Updated User object
        """
        return self.repo.activate_fallback_profile(user_id, fallback_profile_id, reason)

    def deactivate_fallback_profile(self, user_id: str) -> User:
        """Deactivate fallback profile.
        
        Args:
            user_id: User UUID
            
        Returns:
            Updated User object
        """
        return self.repo.deactivate_fallback_profile(user_id)

    def change_password(
        self, 
        user_id: str, 
        old_password: str, 
        new_password: str
    ) -> User:
        """Change user password with verification.
        
        Args:
            user_id: User UUID
            old_password: Current password for verification
            new_password: New password to set
            
        Returns:
            Updated User object
            
        Raises:
            ValueError: If old password incorrect or user not found
        """
        user = self.repo.get_user_by_id(user_id)
        
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        
        if not self.verify_password(old_password, user.password_hash):
            raise ValueError("Incorrect current password")
        
        new_password_hash = self.hash_password(new_password)
        return self.repo.update_user(user_id, password_hash=new_password_hash)

    def suspend_user(self, user_id: str, reason: Optional[str] = None) -> User:
        """Suspend user account.
        
        Args:
            user_id: User UUID
            reason: Reason for suspension
            
        Returns:
            Updated User object
        """
        update_data = {"status": "suspended"}
        if reason:
            update_data["fallback_reason"] = f"Suspended: {reason}"
        
        return self.repo.update_user(user_id, **update_data)

    def activate_user(self, user_id: str) -> User:
        """Activate suspended user account.
        
        Args:
            user_id: User UUID
            
        Returns:
            Updated User object
        """
        return self.repo.update_user(user_id, status="active")