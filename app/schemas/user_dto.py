"""User data transfer objects.

Provides Pydantic schemas for user-related API requests and responses,
including validation rules for user registration, authentication, and profile management.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional, Literal
import re


class UserCreateRequest(BaseModel):
    """User creation request schema.
    
    Validates user registration data with strict username and password requirements.
    
    Attributes:
        username: Unique username (3-50 alphanumeric chars, hyphens, underscores)
        email: Valid email address
        password: Strong password (min 8 chars with upper, lower, digit)
        predefined_profile_id: Optional initial profile assignment
        dynamic_profile_id: Optional dynamic profile reference
        profile_mode: Profile assignment mode (default: COLD_START)
        dynamic_profile_confidence: Confidence score for dynamic profile
        dynamic_profile_ready: Flag indicating dynamic profile readiness
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    predefined_profile_id: Optional[str] = None
    dynamic_profile_id: Optional[str] = None
    profile_mode: Literal["COLD_START", "HYBRID", "DYNAMIC_ONLY", "DRIFT_FALLBACK"] = "COLD_START"
    dynamic_profile_confidence: Optional[float] = 0.0
    dynamic_profile_ready: Optional[bool] = False

    @validator('username')
    def validate_username(cls, v):
        """Ensure username contains only allowed characters."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v

    @validator('password')
    def validate_password(cls, v):
        """Enforce password complexity requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdateRequest(BaseModel):
    """User update request schema.
    
    Allows partial updates to user profile and settings.
    All fields are optional for flexible updates.
    
    Attributes:
        username: Updated username (validated if provided)
        email: Updated email address
        password: Updated password (validated if provided)
        status: Account status (active, suspended, deleted)
        predefined_profile_id: Updated predefined profile assignment
        dynamic_profile_id: Updated dynamic profile reference
        profile_mode: Updated profile assignment mode
        dynamic_profile_confidence: Updated confidence score
        dynamic_profile_ready: Updated readiness flag
        fallback_profile_id: Fallback profile for drift scenarios
        fallback_reason: Reason for fallback activation
        fallback_activated_at: Timestamp of fallback activation
    """
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    status: Optional[Literal["active", "suspended", "deleted"]] = None
    predefined_profile_id: Optional[str] = None
    dynamic_profile_id: Optional[str] = None
    profile_mode: Optional[Literal["COLD_START", "HYBRID", "DYNAMIC_ONLY", "DRIFT_FALLBACK"]] = None
    dynamic_profile_confidence: Optional[float] = None
    dynamic_profile_ready: Optional[bool] = None
    fallback_profile_id: Optional[str] = None
    fallback_reason: Optional[str] = None
    fallback_activated_at: Optional[datetime] = None

    @validator('username')
    def validate_username(cls, v):
        """Ensure username contains only allowed characters."""
        if v is not None and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v

    @validator('password')
    def validate_password(cls, v):
        """Enforce password complexity requirements."""
        if v is not None:
            if len(v) < 8:
                raise ValueError('Password must be at least 8 characters long')
            if not re.search(r'[A-Z]', v):
                raise ValueError('Password must contain at least one uppercase letter')
            if not re.search(r'[a-z]', v):
                raise ValueError('Password must contain at least one lowercase letter')
            if not re.search(r'[0-9]', v):
                raise ValueError('Password must contain at least one digit')
        return v


class UserResponse(BaseModel):
    """User response schema.
    
    Represents user data returned by API endpoints.
    Excludes sensitive information like password hash.
    
    Attributes:
        user_id: Unique user identifier (UUID)
        username: User's display name
        email: User's email address
        created_at: Account creation timestamp
        last_active_at: Last activity timestamp
        status: Current account status
        predefined_profile_id: Assigned predefined profile
        dynamic_profile_id: Generated dynamic profile
        profile_mode: Current profile assignment mode
        dynamic_profile_confidence: Dynamic profile confidence score
        dynamic_profile_ready: Dynamic profile readiness status
        fallback_profile_id: Active fallback profile
        fallback_reason: Reason for fallback usage
        fallback_activated_at: Fallback activation timestamp
    """
    user_id: str
    username: str
    email: str
    created_at: datetime
    last_active_at: Optional[datetime] = None
    status: str
    predefined_profile_id: Optional[str] = None
    dynamic_profile_id: Optional[str] = None
    profile_mode: str
    dynamic_profile_confidence: float
    dynamic_profile_ready: bool
    fallback_profile_id: Optional[str] = None
    fallback_reason: Optional[str] = None
    fallback_activated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Paginated user list response schema.
    
    Attributes:
        total: Total number of users matching query
        users: List of user response objects
    """
    total: int
    users: list[UserResponse]

    class Config:
        from_attributes = True


class UserLoginRequest(BaseModel):
    """User login request schema.
    
    Attributes:
        username: User's username
        password: User's password (plain text, hashed server-side)
    """
    username: str
    password: str


class UserLoginResponse(BaseModel):
    """User login response schema.
    
    Attributes:
        user_id: Authenticated user's unique identifier
        username: Authenticated user's username
        email: Authenticated user's email
        message: Success message
    """
    user_id: str
    username: str
    email: str
    message: str = "Login successful"


class OAuthLoginRequest(BaseModel):
    """OAuth login/registration request schema.
    
    Handles authentication via third-party OAuth providers.
    
    Attributes:
        email: User's email from OAuth provider
        name: User's full name from OAuth provider
        provider: OAuth provider name (google, github, facebook, microsoft, apple)
        provider_id: Unique user identifier from OAuth provider
        picture: Optional profile picture URL
    """
    email: EmailStr
    name: str
    provider: str
    provider_id: str
    picture: Optional[str] = None

    @validator('provider')
    def validate_provider(cls, v):
        """Ensure provider is from allowed list."""
        allowed_providers = ['google', 'github', 'facebook', 'microsoft', 'apple']
        if v.lower() not in allowed_providers:
            raise ValueError(f'OAuth provider must be one of: {", ".join(allowed_providers)}')
        return v.lower()


class OAuthLoginResponse(BaseModel):
    """OAuth login response schema.
    
    Attributes:
        user_id: Authenticated user's unique identifier
        username: User's username
        email: User's email address
        name: User's full name
        picture: Profile picture URL
        is_new_user: Flag indicating if account was just created
        access_token: JWT access token for API authentication
        token_type: Token type (always "bearer")
    """
    user_id: str
    username: str
    email: str
    name: str
    picture: Optional[str] = None
    is_new_user: bool
    access_token: str
    token_type: str = "bearer"


class GitHubCallbackRequest(BaseModel):
    """GitHub OAuth callback request schema.
    
    Attributes:
        code: Authorization code from GitHub OAuth flow
        redirect_uri: OAuth callback redirect URI
    """
    code: str
    redirect_uri: str