# app/api/user_routes.py

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
    UserLoginResponse
)
from pydantic import BaseModel


router = APIRouter(
    prefix="/api/users",
    tags=["users"]
)


# Dependency
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


# Helper function to convert User model to UserResponse
def to_user_response(user) -> dict:
    """Convert User model to response dict"""
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
    """Register a new user"""
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


# ==================== CRUD Routes ====================

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service)
):
    """Get user by ID"""
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
    """Get all users with pagination and filtering"""
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
    """Get user by username"""
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
    """Get user by email"""
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
    """Update user"""
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
    """Delete user (soft or hard delete)"""
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


# ==================== Password Management ====================

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/{user_id}/change-password", response_model=UserResponse)
def change_password(
    user_id: str,
    password_data: PasswordChangeRequest,
    service: UserService = Depends(get_user_service)
):
    """Change user password"""
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


# ==================== Account Status Management ====================

@router.post("/{user_id}/suspend", response_model=UserResponse)
def suspend_user(
    user_id: str,
    reason: str = Query(None),
    service: UserService = Depends(get_user_service)
):
    """Suspend user account"""
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
    """Activate suspended user account"""
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


# ==================== Profile Management ====================

@router.post("/{user_id}/fallback/activate", response_model=UserResponse)
def activate_fallback(
    user_id: str,
    fallback_profile_id: str = Query(...),
    reason: str = Query(...),
    service: UserService = Depends(get_user_service)
):
    """Activate fallback profile for drift handling"""
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
    """Deactivate fallback profile"""
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