"""User API Routes Module.

This module provides RESTful API endpoints for user management operations including:
- User registration and authentication (traditional and OAuth)
- User account CRUD operations  
- Password management
- Account status management (activation, suspension)
- Fallback profile management for drift handling

All endpoints follow REST conventions with appropriate HTTP status codes,
error handling, and response models for type safety.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.user_service import UserService
from app.schemas.user_dto import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserListResponse,
    UserLoginRequest,
    UserLoginResponse,
    OAuthLoginRequest,
    OAuthLoginResponse,
    GitHubCallbackRequest
)
from app.core.jwt_utils import create_access_token
from app.core.config import settings
import httpx
from pydantic import BaseModel


router = APIRouter(
    prefix="/api/users",
    tags=["users"]
)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency injection for UserService.
    
    Args:
        db: Database session injected by FastAPI.
        
    Returns:
        UserService: Configured user service instance.
    """
    return UserService(db)


def to_user_response(user) -> dict:
    """Convert User ORM model to UserResponse dictionary.
    
    Args:
        user: User ORM model instance.
        
    Returns:
        dict: User data formatted for API response with all fields properly serialized.
    """
    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at,
        "last_active_at": user.last_active_at,
        "status": user.status.value if hasattr(user.status, 'value') else user.status,
        "predefined_profile_id": user.predefined_profile_id,
        "dynamic_profile_id": user.dynamic_profile_id,
        "profile_mode": user.profile_mode.value if hasattr(user.profile_mode, 'value') else user.profile_mode,
        "dynamic_profile_confidence": float(user.dynamic_profile_confidence),
        "dynamic_profile_ready": user.dynamic_profile_ready == "true",
        "fallback_profile_id": user.fallback_profile_id,
        "fallback_reason": user.fallback_reason,
        "fallback_activated_at": user.fallback_activated_at
    }


# ==================== Authentication Routes ====================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserCreateRequest,
    service: UserService = Depends(get_user_service)
):
    """Register a new user account.
    
    Creates a new user with username, email, and password. Validates uniqueness
    of username and email before creating the account.
    
    Args:
        user_data: User registration data (username, email, password).
        service: Injected UserService dependency.
        
    Returns:
        UserResponse: Created user data.
        
    Raises:
        HTTPException 400: If username/email already exists or validation fails.
        HTTPException 500: If user creation fails due to server error.
    """
    try:
        user = service.create_user(user_data)
        return to_user_response(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )


@router.post("/login", response_model=UserLoginResponse)
def login_user(
    login_data: UserLoginRequest,
    service: UserService = Depends(get_user_service)
):
    """Authenticate a user"""
    try:
        user = service.authenticate_user(login_data)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        return UserLoginResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/oauth/login", response_model=OAuthLoginResponse)
def oauth_login(
    oauth_data: OAuthLoginRequest,
    service: UserService = Depends(get_user_service)
):
    """
    OAuth login or registration endpoint
    
    If user exists with the email or provider credentials: logs them in
    If user doesn't exist: creates account and logs them in
    Returns is_new_user flag to indicate if user should complete onboarding
    """
    try:
        # Call the OAuth login/register service
        user, is_new_user = service.oauth_login_or_register(
            email=oauth_data.email,
            name=oauth_data.name,
            provider=oauth_data.provider,
            provider_id=oauth_data.provider_id,
            picture=oauth_data.picture
        )
        
        # Generate JWT access token
        access_token = create_access_token(data={"sub": user.user_id})
        
        # Return response with user data and token
        return OAuthLoginResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            name=user.name or "",
            picture=user.picture,
            is_new_user=is_new_user,
            access_token=access_token,
            token_type="bearer"
        )
        
    except ValueError as e:
        # Handle unique constraint violations
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth authentication failed: {str(e)}"
        )


@router.post("/oauth/github/callback", response_model=OAuthLoginResponse)
async def github_oauth_callback(
    request: GitHubCallbackRequest,
    service: UserService = Depends(get_user_service)
):
    """Handle GitHub OAuth callback and complete authentication flow.
    
    Exchanges authorization code for GitHub access token, fetches user profile
    data from GitHub API, retrieves verified email, and creates or authenticates
    user account. Returns JWT token for authenticated session.
    
    Args:
        request: GitHub callback data (authorization code and redirect URI).
        service: Injected UserService dependency.
        
    Returns:
        OAuthLoginResponse: User data with JWT token and new user flag.
        
    Raises:
        HTTPException 500: If GitHub OAuth is not configured on server.
        HTTPException 400: If code exchange fails or no verified email found.
        HTTPException 500: If GitHub API calls or user creation fails.
    """
    GITHUB_CLIENT_ID = settings.GITHUB_CLIENT_ID
    GITHUB_CLIENT_SECRET = settings.GITHUB_CLIENT_SECRET
    
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub OAuth not configured on server"
        )
    
    try:
        async with httpx.AsyncClient() as client:
            # Step 1: Exchange code for access token
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": GITHUB_CLIENT_ID,
                    "client_secret": GITHUB_CLIENT_SECRET,
                    "code": request.code,
                    "redirect_uri": request.redirect_uri,
                }
            )
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to exchange code for access token: {token_response.text}"
                )
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                error_description = token_data.get("error_description", "No access token received")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"GitHub OAuth error: {error_description}"
                )
            
            # Step 2: Get user info from GitHub
            user_response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                }
            )
            
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info from GitHub"
                )
            
            github_user = user_response.json()
            
            # Step 3: Get email if not in profile
            email = github_user.get("email")
            if not email:
                emails_response = await client.get(
                    "https://api.github.com/user/emails",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github+json",
                    }
                )
                
                if emails_response.status_code == 200:
                    emails = emails_response.json()
                    # Find primary verified email
                    for email_data in emails:
                        if email_data.get("primary") and email_data.get("verified"):
                            email = email_data.get("email")
                            break
                    
                    # If no primary, use first verified email
                    if not email:
                        for email_data in emails:
                            if email_data.get("verified"):
                                email = email_data.get("email")
                                break
            
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No verified email found in GitHub account. Please make your email public in GitHub settings."
                )
        
        # Step 4: Authenticate or create user
        user, is_new_user = service.oauth_login_or_register(
            email=email,
            name=github_user.get("name") or github_user.get("login"),
            provider="github",
            provider_id=str(github_user.get("id")),
            picture=github_user.get("avatar_url")
        )
        
        # Generate JWT access token
        jwt_token = create_access_token(data={"sub": user.user_id})
        
        # Return response with user data and token
        return OAuthLoginResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            name=user.name or "",
            picture=user.picture,
            is_new_user=is_new_user,
            access_token=jwt_token,
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GitHub OAuth failed: {str(e)}"
        )



@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service)
):
    """Retrieve user by unique identifier.
    
    Args:
        user_id: Unique user identifier (UUID).
        service: Injected UserService dependency.
        
    Returns:
        UserResponse: Complete user data.
        
    Raises:
        HTTPException 404: If user with given ID does not exist.
    """
    user = service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    return to_user_response(user)


@router.get("/", response_model=UserListResponse)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: str = Query(None),
    search: str = Query(None),
    service: UserService = Depends(get_user_service)
):
    """List all users with pagination and optional filtering.
    
    Supports pagination via skip/limit and filtering by user status or search term
    (matches username/email).
    
    Args:
        skip: Number of records to skip (default: 0).
        limit: Maximum number of records to return (default: 100, max: 1000).
        status: Optional status filter (active/inactive/suspended).
        search: Optional search term for username/email matching.
        service: Injected UserService dependency.
        
    Returns:
        UserListResponse: Paginated list of users with total count.
        
    Raises:
        HTTPException 500: If database query fails.
    """
    try:
        users, total = service.list_users(skip=skip, limit=limit, status=status, search=search)
        user_responses = [to_user_response(user) for user in users]
        return UserListResponse(total=total, users=user_responses)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/username/{username}", response_model=UserResponse)
def get_user_by_username(
    username: str,
    service: UserService = Depends(get_user_service)
):
    """Retrieve user by username.
    
    Args:
        username: Unique username.
        service: Injected UserService dependency.
        
    Returns:
        UserResponse: Complete user data.
        
    Raises:
        HTTPException 404: If user with given username does not exist.
    """
    user = service.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username '{username}' not found"
        )
    return to_user_response(user)


@router.get("/email/{email}", response_model=UserResponse)
def get_user_by_email(
    email: str,
    service: UserService = Depends(get_user_service)
):
    """Retrieve user by email address.
    
    Args:
        email: User's email address.
        service: Injected UserService dependency.
        
    Returns:
        UserResponse: Complete user data.
        
    Raises:
        HTTPException 404: If user with given email does not exist.
    """
    user = service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{email}' not found"
        )
    return to_user_response(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    user_data: UserUpdateRequest,
    service: UserService = Depends(get_user_service)
):
    """Update user account information.
    
    Updates user fields such as username, email, or profile associations.
    Only provided fields are updated (partial update).
    
    Args:
        user_id: Unique user identifier.
        user_data: Updated user fields.
        service: Injected UserService dependency.
        
    Returns:
        UserResponse: Updated user data.
        
    Raises:
        HTTPException 400: If validation fails (e.g., duplicate username/email).
        HTTPException 500: If update operation fails.
    """
    try:
        user = service.update_user(user_id, user_data)
        return to_user_response(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    hard_delete: bool = Query(False),
    service: UserService = Depends(get_user_service)
):
    """Delete user account (soft or hard delete).
    
    Supports both soft delete (marks as deleted, preserves data) and hard delete
    (permanent removal from database).
    
    Args:
        user_id: Unique user identifier.
        hard_delete: If True, permanently removes user; if False, soft deletes (default: False).
        service: Injected UserService dependency.
        
    Returns:
        None: No content on successful deletion (204 status).
        
    Raises:
        HTTPException 404: If user does not exist.
        HTTPException 500: If deletion operation fails.
    """
    try:
        service.delete_user(user_id, hard_delete=hard_delete)
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


class PasswordChangeRequest(BaseModel):
    """Request model for password change operation."""
    old_password: str
    new_password: str


@router.post("/{user_id}/change-password", response_model=UserResponse)
def change_password(
    user_id: str,
    password_data: PasswordChangeRequest,
    service: UserService = Depends(get_user_service)
):
    """Change user password with verification.
    
    Validates old password before setting new password. Requires both old and new
    passwords for security.
    
    Args:
        user_id: Unique user identifier.
        password_data: Old and new passwords.
        service: Injected UserService dependency.
        
    Returns:
        UserResponse: Updated user data.
        
    Raises:
        HTTPException 400: If old password is incorrect or validation fails.
        HTTPException 500: If password change operation fails.
    """
    try:
        user = service.change_password(
            user_id,
            password_data.old_password,
            password_data.new_password
        )
        return to_user_response(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )


@router.post("/{user_id}/suspend", response_model=UserResponse)
def suspend_user(
    user_id: str,
    reason: str = Query(None),
    service: UserService = Depends(get_user_service)
):
    """Suspend user account.
    
    Marks user account as suspended, preventing login and access. Optionally
    records reason for suspension.
    
    Args:
        user_id: Unique user identifier.
        reason: Optional reason for suspension.
        service: Injected UserService dependency.
        
    Returns:
        UserResponse: Updated user data with suspended status.
        
    Raises:
        HTTPException 404: If user does not exist.
        HTTPException 500: If suspension operation fails.
    """
    try:
        user = service.suspend_user(user_id, reason)
        return to_user_response(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suspend user: {str(e)}"
        )


@router.post("/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: str,
    service: UserService = Depends(get_user_service)
):
    """Activate suspended user account.
    
    Restores access to previously suspended user account by changing status
    back to active.
    
    Args:
        user_id: Unique user identifier.
        service: Injected UserService dependency.
        
    Returns:
        UserResponse: Updated user data with active status.
        
    Raises:
        HTTPException 404: If user does not exist.
        HTTPException 500: If activation operation fails.
    """
    try:
        user = service.activate_user(user_id)
        return to_user_response(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate user: {str(e)}"
        )


@router.post("/{user_id}/fallback/activate", response_model=UserResponse)
def activate_fallback(
    user_id: str,
    fallback_profile_id: str = Query(...),
    reason: str = Query(...),
    service: UserService = Depends(get_user_service)
):
    """Activate fallback profile for drift handling.
    
    Sets a fallback predefined profile when user's behavior drifts significantly
    from assigned profile. Used for maintaining system stability during behavioral
    inconsistencies.
    
    Args:
        user_id: Unique user identifier.
        fallback_profile_id: ID of predefined profile to use as fallback.
        reason: Reason for activating fallback (e.g., drift detected).
        service: Injected UserService dependency.
        
    Returns:
        UserResponse: Updated user data with fallback profile activated.
        
    Raises:
        HTTPException 404: If user or profile does not exist.
        HTTPException 500: If activation operation fails.
    """
    try:
        user = service.activate_fallback_profile(user_id, fallback_profile_id, reason)
        return to_user_response(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate fallback: {str(e)}"
        )


@router.post("/{user_id}/fallback/deactivate", response_model=UserResponse)
def deactivate_fallback(
    user_id: str,
    service: UserService = Depends(get_user_service)
):
    """Deactivate fallback profile.
    
    Removes fallback profile assignment, returning user to normal profile mode
    after drift situation resolves.
    
    Args:
        user_id: Unique user identifier.
        service: Injected UserService dependency.
        
    Returns:
        UserResponse: Updated user data with fallback profile removed.
        
    Raises:
        HTTPException 404: If user does not exist.
        HTTPException 500: If deactivation operation fails.
    """
    try:
        user = service.deactivate_fallback_profile(user_id)
        return to_user_response(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate fallback: {str(e)}"
        )