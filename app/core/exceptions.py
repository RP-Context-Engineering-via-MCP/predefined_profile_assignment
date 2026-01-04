# app/core/exceptions.py

"""
Custom exception classes for the application.
Provides better error handling and more specific exception types.
"""

from typing import Optional


# ==================== Base Exceptions ====================

class ApplicationError(Exception):
    """Base exception for all application errors."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# ==================== User-Related Exceptions ====================

class UserError(ApplicationError):
    """Base exception for user-related errors."""
    pass


class UserNotFoundError(UserError):
    """Raised when a user is not found."""
    
    def __init__(self, user_id: Optional[str] = None, username: Optional[str] = None, email: Optional[str] = None):
        identifier = user_id or username or email or "Unknown"
        message = f"User not found: {identifier}"
        super().__init__(message, {"user_id": user_id, "username": username, "email": email})


class UserAlreadyExistsError(UserError):
    """Raised when attempting to create a user that already exists."""
    
    def __init__(self, field: str, value: str):
        message = f"User with {field} '{value}' already exists"
        super().__init__(message, {"field": field, "value": value})


class InvalidCredentialsError(UserError):
    """Raised when user credentials are invalid."""
    
    def __init__(self):
        message = "Invalid username or password"
        super().__init__(message)


class UserSuspendedError(UserError):
    """Raised when attempting to access a suspended user account."""
    
    def __init__(self, user_id: str):
        message = f"User account is suspended: {user_id}"
        super().__init__(message, {"user_id": user_id})


# ==================== Profile-Related Exceptions ====================

class ProfileError(ApplicationError):
    """Base exception for profile-related errors."""
    pass


class ProfileNotFoundError(ProfileError):
    """Raised when a profile is not found."""
    
    def __init__(self, profile_id: str):
        message = f"Profile not found: {profile_id}"
        super().__init__(message, {"profile_id": profile_id})


class InsufficientDataError(ProfileError):
    """Raised when there's insufficient data for profile assignment."""
    
    def __init__(self, required_prompts: int, actual_prompts: int):
        message = f"Insufficient data for profile assignment. Required: {required_prompts}, Actual: {actual_prompts}"
        super().__init__(message, {"required_prompts": required_prompts, "actual_prompts": actual_prompts})


class ProfileAssignmentError(ProfileError):
    """Raised when profile assignment fails."""
    
    def __init__(self, reason: str, details: Optional[dict] = None):
        message = f"Profile assignment failed: {reason}"
        super().__init__(message, details)


# ==================== Validation Exceptions ====================

class ValidationError(ApplicationError):
    """Base exception for validation errors."""
    pass


class InvalidEmailError(ValidationError):
    """Raised when email format is invalid."""
    
    def __init__(self, email: str):
        message = f"Invalid email format: {email}"
        super().__init__(message, {"email": email})


class InvalidPasswordError(ValidationError):
    """Raised when password doesn't meet requirements."""
    
    def __init__(self, reason: str):
        message = f"Invalid password: {reason}"
        super().__init__(message, {"reason": reason})


class InvalidUsernameError(ValidationError):
    """Raised when username doesn't meet requirements."""
    
    def __init__(self, username: str, reason: str):
        message = f"Invalid username '{username}': {reason}"
        super().__init__(message, {"username": username, "reason": reason})


# ==================== Database Exceptions ====================

class DatabaseError(ApplicationError):
    """Base exception for database-related errors."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    
    def __init__(self, details: Optional[str] = None):
        message = "Database connection failed"
        super().__init__(message, {"details": details})


class DataIntegrityError(DatabaseError):
    """Raised when data integrity constraint is violated."""
    
    def __init__(self, constraint: str, details: Optional[str] = None):
        message = f"Data integrity violation: {constraint}"
        super().__init__(message, {"constraint": constraint, "details": details})


# ==================== Authentication Exceptions ====================

class AuthenticationError(ApplicationError):
    """Base exception for authentication-related errors."""
    pass


class TokenError(AuthenticationError):
    """Raised when JWT token is invalid or expired."""
    
    def __init__(self, reason: str):
        message = f"Token error: {reason}"
        super().__init__(message, {"reason": reason})


class OAuthError(AuthenticationError):
    """Raised when OAuth authentication fails."""
    
    def __init__(self, provider: str, reason: str):
        message = f"OAuth authentication failed for {provider}: {reason}"
        super().__init__(message, {"provider": provider, "reason": reason})


# ==================== Configuration Exceptions ====================

class ConfigurationError(ApplicationError):
    """Raised when application configuration is invalid."""
    
    def __init__(self, setting: str, reason: str):
        message = f"Configuration error for '{setting}': {reason}"
        super().__init__(message, {"setting": setting, "reason": reason})
