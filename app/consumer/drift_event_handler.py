"""Drift Event Handler.

Processes drift events received from the Drift Detection Service.
Filters by severity, fetches recent behaviors from Behavior Resolution,
and triggers profile re-assignment via the IntakeOrchestrator.
"""

import logging
import httpx
from typing import Optional, List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

# Only act on drift events with these severities
ACTIONABLE_SEVERITIES = {"MODERATE", "STRONG"}


class DriftEventHandler:
    """Handles drift events from the Drift Detection Service.
    
    When a user's behavior drifts significantly from their assigned profile,
    this handler triggers a profile re-evaluation using recent behavior data.
    
    Flow:
    1. Receive drift event from Redis Stream
    2. Filter by severity (only MODERATE/STRONG trigger action)
    3. Fetch recent behaviors from Behavior Resolution Service
    4. Pass to IntakeOrchestrator in DRIFT_FALLBACK mode
    """

    def __init__(self):
        """Initialize handler.
        
        IntakeOrchestrator is imported lazily to avoid circular imports.
        """
        self._orchestrator = None

    def _get_orchestrator(self):
        """Lazy load IntakeOrchestrator to avoid circular imports."""
        if self._orchestrator is None:
            from app.core.intake_orchestrator import IntakeOrchestrator
            self._orchestrator = IntakeOrchestrator()
        return self._orchestrator

    async def handle(self, event: Dict[str, Any]):
        """Handle a drift event.
        
        Processes drift events from the drift.events Redis Stream.
        Only acts on MODERATE or STRONG severity drifts.
        
        Args:
            event: Drift event dict with shape:
                {
                    "drift_event_id": "drift-evt-abc123",
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "severity": "STRONG"
                }
                
                Fields:
                - drift_event_id: Traceability ID for logging and including
                  in the profile.assigned event published afterward.
                - user_id: Required to call Behavior Resolution Service
                  (GET /api/behaviors/{user_id}/recent).
                - severity: Gate for reassignment. MODERATE or STRONG triggers
                  action; WEAK is ignored. Filter happens here, not upstream.
        """
        severity = event.get("severity", "WEAK")
        user_id = event.get("user_id")
        drift_event_id = event.get("drift_event_id")

        # Only act on actionable drift severities
        if severity not in ACTIONABLE_SEVERITIES:
            logger.debug(
                f"Skipping drift event {drift_event_id}: "
                f"severity {severity} not actionable"
            )
            return

        if not user_id:
            logger.warning(f"Drift event {drift_event_id} missing user_id")
            return

        logger.info(
            f"Processing drift event: user={user_id}, "
            f"severity={severity}, drift_id={drift_event_id}"
        )

        # Fetch recent behaviors from Behavior Resolution Service
        recent_behaviors = await self._fetch_recent_behaviors(user_id)
        if not recent_behaviors:
            logger.warning(
                f"No recent behaviors found for user {user_id}, "
                f"skipping drift fallback"
            )
            return

        # Hand off to orchestrator in DRIFT_FALLBACK mode
        orchestrator = self._get_orchestrator()
        result = await orchestrator.process(
            user_id=user_id,
            mode="DRIFT_FALLBACK",
            extracted_behavior=recent_behaviors,
            trigger_event_id=drift_event_id
        )

        logger.info(
            f"Drift fallback result for user {user_id}: "
            f"status={result.get('status')}, "
            f"profile={result.get('assigned_profile_id')}"
        )

    async def _fetch_recent_behaviors(
        self, 
        user_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch recent behavior signals from Behavior Resolution Service.
        
        Calls the Behavior Resolution Service API to retrieve the last N
        profile_signals payloads for the user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List of extracted_behavior dicts, or None on failure.
            Each dict contains:
                {
                    "intents": {"LEARNING": 0.8, ...},
                    "interests": {"PROGRAMMING": 0.7, ...},
                    "behavior_level": "INTERMEDIATE",
                    "signals": {"DETAILED_EXPLANATION": 0.5, ...},
                    "complexity": 0.65,
                    "consistency": 0.72
                }
        """
        url = (
            f"{settings.BEHAVIOR_RESOLUTION_BASE_URL}"
            f"/api/behaviors/{user_id}/recent"
        )
        params = {"limit": settings.DRIFT_FALLBACK_BEHAVIOR_LIMIT}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                behaviors = data.get("behaviors", [])
                logger.debug(
                    f"Fetched {len(behaviors)} recent behaviors for user {user_id}"
                )
                return behaviors
                
        except httpx.TimeoutException:
            logger.error(
                f"Timeout fetching behaviors for user {user_id} "
                f"from {settings.BEHAVIOR_RESOLUTION_BASE_URL}"
            )
            return None
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error fetching behaviors for user {user_id}: "
                f"{e.response.status_code}"
            )
            return None
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to fetch behaviors for user {user_id}: {e}"
            )
            return None
