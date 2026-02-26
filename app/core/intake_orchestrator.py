"""Intake Orchestrator for Profile Assignment.

Central entry point that routes profile assignment requests to the correct
mode (COLD_START or DRIFT_FALLBACK), delegates to ProfileAssigner, and
publishes assignment events when profiles are successfully assigned.
"""

import logging
from typing import Union, List, Dict, Any, Optional
from app.services.profile_assigner import ProfileAssigner
from app.publisher.profile_publisher import ProfilePublisher
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class IntakeOrchestrator:
    """Central orchestrator for all profile assignment requests.
    
    Routes incoming requests from both HTTP API (cold start) and
    Redis consumer (drift fallback) to the ProfileAssigner, then
    publishes assignment events to downstream services.
    
    Flow:
    1. Receive assignment request with user_id, mode, extracted_behavior
    2. Create database session and ProfileAssigner
    3. Delegate to ProfileAssigner.assign()
    4. If profile assigned, publish event via ProfilePublisher
    5. Return assignment result
    
    Attributes:
        _publisher: ProfilePublisher for emitting assignment events
    """

    def __init__(self):
        """Initialize orchestrator with publisher."""
        self._publisher = ProfilePublisher()

    async def process(
        self,
        user_id: str,
        mode: str,
        extracted_behavior: Union[Dict[str, Any], List[Dict[str, Any]]],
        trigger_event_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a profile assignment request.
        
        Central entry point for all profile assignment requests. Handles
        both cold-start (single behavior) and drift-fallback (multiple
        behaviors) scenarios.
        
        Args:
            user_id: UUID of the target user
            mode: Assignment mode - "COLD_START" or "DRIFT_FALLBACK"
            extracted_behavior: Behavior signals from Behavior Resolution.
                - COLD_START: Single dict with intents, interests, signals, etc.
                - DRIFT_FALLBACK: List of dicts (recent prompts)
            trigger_event_id: Drift event ID if triggered by drift detection
            
        Returns:
            Assignment result dict containing:
                - status: "ASSIGNED" or "PENDING"
                - confidence_level: "HIGH", "MEDIUM", or "LOW"
                - user_mode: Mode used for assignment
                - prompt_count: Total prompts processed
                - assigned_profile_id: Profile ID if assigned, else None
                - aggregated_rankings: List of profile ranking states
                
        Raises:
            ValueError: If user not found or behavior format invalid
        """
        logger.info(
            f"Processing profile assignment: user={user_id}, mode={mode}, "
            f"trigger={trigger_event_id}"
        )

        # Create database session and ProfileAssigner
        # Using sync session since ProfileAssigner is synchronous
        db = SessionLocal()
        try:
            assigner = ProfileAssigner(db)
            
            # Delegate to ProfileAssigner
            result = assigner.assign(
                extracted_behavior=extracted_behavior,
                user_id=user_id
            )
            
            # Commit any changes made by assigner
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"Profile assignment failed for user {user_id}: {e}")
            raise
        finally:
            db.close()

        # If profile was assigned, publish the event
        if result.get("status") == "ASSIGNED":
            try:
                await self._publisher.publish(
                    user_id=user_id,
                    assigned_profile_id=result["assigned_profile_id"],
                    confidence_level=result["confidence_level"],
                    mode=mode,
                    trigger_event_id=trigger_event_id
                )
                logger.info(
                    f"Published profile assignment: user={user_id}, "
                    f"profile={result['assigned_profile_id']}"
                )
            except Exception as e:
                # Log but don't fail - assignment is already persisted
                logger.error(
                    f"Failed to publish assignment event for user {user_id}: {e}"
                )

        return result

    def process_sync(
        self,
        user_id: str,
        mode: str,
        extracted_behavior: Union[Dict[str, Any], List[Dict[str, Any]]],
        trigger_event_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronous version of process for non-async contexts.
        
        Same as process() but without publishing events.
        Use this when called from synchronous code that cannot await.
        
        Args:
            user_id: UUID of the target user
            mode: Assignment mode - "COLD_START" or "DRIFT_FALLBACK"
            extracted_behavior: Behavior signals from Behavior Resolution
            trigger_event_id: Drift event ID if triggered by drift detection
            
        Returns:
            Assignment result dict (same structure as process())
        """
        logger.info(
            f"Processing profile assignment (sync): user={user_id}, mode={mode}"
        )

        db = SessionLocal()
        try:
            assigner = ProfileAssigner(db)
            result = assigner.assign(
                extracted_behavior=extracted_behavior,
                user_id=user_id
            )
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Profile assignment failed for user {user_id}: {e}")
            raise
        finally:
            db.close()

        # Note: Cannot publish in sync mode - caller must handle publishing
        if result.get("status") == "ASSIGNED":
            logger.warning(
                f"Profile assigned in sync mode - event not published. "
                f"user={user_id}, profile={result['assigned_profile_id']}"
            )

        return result

    async def get_status(self, user_id: str) -> Dict[str, Any]:
        """Get current profile assignment status without triggering scoring.
        
        Retrieves the current assignment state for a user including
        confidence level, mode, and ranking statistics.
        
        Args:
            user_id: UUID of the target user
            
        Returns:
            Assignment status dict or None if user not found
        """
        db = SessionLocal()
        try:
            assigner = ProfileAssigner(db)
            status = assigner.get_assignment_status(user_id)
            return status
        finally:
            db.close()

    async def close(self):
        """Close publisher connection.
        
        Should be called during application shutdown.
        """
        await self._publisher.close()
