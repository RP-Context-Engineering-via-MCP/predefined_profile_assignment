# app/schemas/user_dto.py

from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional, Literal
import re


class UserCreateRequest(BaseModel):
    """Schema for creating a new user"""
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
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
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
    """Schema for updating a user"""
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
        """Validate username format"""
        if v is not None and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
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
    """Schema for user response (without password)"""
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
    """Schema for user list response"""
    total: int
    users: list[UserResponse]

    class Config:
        from_attributes = True


class UserLoginRequest(BaseModel):
    """Schema for user login"""
    username: str
    password: str


class UserLoginResponse(BaseModel):
    """Schema for login response"""
    user_id: str
    username: str
    email: str
    message: str = "Login successful"


class OAuthLoginRequest(BaseModel):
    """Schema for OAuth login/registration"""
    email: EmailStr
    name: str
    provider: str  # 'google', 'github', 'facebook', etc.
    provider_id: str  # OAuth provider's unique user ID
    picture: Optional[str] = None  # Profile picture URL

    @validator('provider')
    def validate_provider(cls, v):
        """Validate OAuth provider"""
        allowed_providers = ['google', 'github', 'facebook', 'microsoft', 'apple']
        if v.lower() not in allowed_providers:
            raise ValueError(f'OAuth provider must be one of: {", ".join(allowed_providers)}')
        return v.lower()


class OAuthLoginResponse(BaseModel):
    """Schema for OAuth login response"""
    user_id: str
    username: str
    email: str
    name: str
    picture: Optional[str] = None
    is_new_user: bool
    access_token: str
    token_type: str = "bearer"


class GitHubCallbackRequest(BaseModel):
    """Schema for GitHub OAuth callback request"""
    code: str
    redirect_uri: str