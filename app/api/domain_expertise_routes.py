"""Domain Expertise API Routes.

Endpoints for managing user domain expertise tracking and updates.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services.domain_expertise_service import DomainExpertiseService
from app.schemas.domain_expertise_dto import (
    DomainExpertiseStateResponse,
    DomainExpertiseUpdateRequest,
    DomainExpertiseUpdateResponse,
    DomainExpertiseInitRequest,
    DomainExpertiseInitResponse,
    UserDomainStatesResponse,
    ExpertiseDecayRequest,
    ExpertiseDecayResponse
)


router = APIRouter(
    prefix="/api/domain-expertise",
    tags=["Domain Expertise"]
)


@router.post("/update", response_model=DomainExpertiseUpdateResponse, status_code=status.HTTP_200_OK)
def update_domain_expertise(
    request: DomainExpertiseUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update user expertise for a specific domain based on prompt analysis.
    
    Analyzes the user's prompt for expertise signals and updates their
    confidence score and expertise level accordingly.
    
    Args:
        request: Update request with user_id, interest_id, and prompt
        db: Database session
        
    Returns:
        Update details including confidence changes and detected signals
        
    Raises:
        HTTPException: If update is not applicable (e.g., trivial prompt)
    """
    service = DomainExpertiseService(db)
    
    result = service.update_user_expertise(
        user_id=request.user_id,
        interest_id=request.interest_id,
        prompt=request.prompt,
        complexity_score=request.complexity_score
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt does not warrant expertise update (too trivial or acknowledgement)"
        )
    
    return result


@router.get("/user/{user_id}/domain/{interest_id}", response_model=DomainExpertiseStateResponse)
def get_user_domain_expertise(
    user_id: str,
    interest_id: int,
    db: Session = Depends(get_db)
):
    """Get user's expertise state for a specific domain.
    
    Args:
        user_id: User identifier
        interest_id: Interest domain identifier
        db: Database session
        
    Returns:
        Current expertise state
        
    Raises:
        HTTPException: If state not found
    """
    service = DomainExpertiseService(db)
    result = service.get_user_expertise(user_id, interest_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No expertise state found for user {user_id} in domain {interest_id}"
        )
    
    return result


@router.get("/user/{user_id}", response_model=UserDomainStatesResponse)
def get_all_user_domain_expertise(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get all domain expertise states for a user.
    
    Args:
        user_id: User identifier
        db: Database session
        
    Returns:
        List of all domain expertise states
    """
    service = DomainExpertiseService(db)
    states = service.get_user_expertise(user_id)
    
    if not states:
        states = []
    
    return {
        "user_id": user_id,
        "domain_states": states,
        "total_domains": len(states)
    }


@router.post("/initialize", response_model=DomainExpertiseInitResponse, status_code=status.HTTP_201_CREATED)
def initialize_domain_expertise(
    request: DomainExpertiseInitRequest,
    db: Session = Depends(get_db)
):
    """Initialize expertise tracking for a new user-domain pair.
    
    Sets up cold-start state with beginner level and low confidence.
    
    Args:
        request: Initialization request with user_id and interest_id
        db: Database session
        
    Returns:
        Initialized state details
    """
    service = DomainExpertiseService(db)
    result = service.initialize_cold_start(
        user_id=request.user_id,
        interest_id=request.interest_id
    )
    
    return result


@router.post("/decay", response_model=ExpertiseDecayResponse)
def apply_expertise_decay(
    request: ExpertiseDecayRequest,
    db: Session = Depends(get_db)
):
    """Apply time-based decay to inactive domain expertise states.
    
    This endpoint should be called periodically (e.g., via cron job)
    to handle expertise drift for domains that haven't been used recently.
    
    Args:
        request: Decay configuration (days threshold and decay factor)
        db: Database session
        
    Returns:
        Number of records updated
    """
    service = DomainExpertiseService(db)
    records_updated = service.apply_decay_to_inactive_domains()
    
    return {
        "records_updated": records_updated,
        "success": True
    }
