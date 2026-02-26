# Schemas package initialization
"""Data Transfer Objects (DTOs) for API request/response validation.

This module provides Pydantic models for validating API payloads
and serializing responses.
"""

from app.schemas.predefined_profile_dto import (
    BehaviorInputDTO,
    AssignProfileRequest,
    AssignmentStatusResponse
)

__all__ = [
    "BehaviorInputDTO",
    "AssignProfileRequest",
    "AssignmentStatusResponse"
]
