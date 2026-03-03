"""Drift Event Handler.

Processes drift events received from the Drift Detection Service.
Filters by severity, fetches specific behaviors by IDs from Behavior Resolution Service,
and triggers profile re-assignment via the IntakeOrchestrator.
"""

import logging
import httpx
from typing import Optional, List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

# Only act on drift events with these severities
ACTIONABLE_SEVERITIES = {"MODERATE_DRIFT", "STRONG_DRIFT"}


class DriftEventHandler:
    """Handles drift events from the Drift Detection Service.
    
    When a user's behavior drifts significantly from their assigned profile,
    this handler triggers a profile re-evaluation using specific behavior data.
    
    Flow:
    1. Receive drift event from Redis Stream with behavior_ref_ids
    2. Filter by severity (only MODERATE_DRIFT/STRONG_DRIFT trigger action)
    3. Fetch specific behaviors by IDs from Behavior Resolution Service
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
        Only acts on MODERATE_DRIFT or STRONG_DRIFT severity drifts.
        
        Args:
            event: Drift event dict with shape:
                {
                    "drift_event_id": "drift-abc123",
                    "user_id": "user_001",
                    "severity": "STRONG_DRIFT",
                    "behavior_ref_ids": ["beh_r_001", "beh_r_002", "beh_c_003"]
                }
                
                Fields:
                - drift_event_id: Traceability ID for logging and including
                  in the profile.assigned event published afterward.
                - user_id: Required to identify the user for profile reassignment.
                - severity: Gate for reassignment. MODERATE_DRIFT or STRONG_DRIFT
                  triggers action; NO_DRIFT and WEAK_DRIFT are ignored.
                  Filter happens here, not upstream.
                - behavior_ref_ids: List of behavior IDs that triggered the drift.
                  Used to fetch specific behaviors from Behavior Resolution Service.
        """
        severity = event.get("severity", "NO_DRIFT")
        user_id = event.get("user_id")
        drift_event_id = event.get("drift_event_id")
        behavior_ref_ids = event.get("behavior_ref_ids", [])

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

        if not behavior_ref_ids:
            logger.warning(
                f"Drift event {drift_event_id} missing behavior_ref_ids, "
                f"skipping drift fallback"
            )
            return

        logger.info(
            f"✅ Processing drift event: user={user_id}, "
            f"severity={severity}, drift_id={drift_event_id}, "
            f"behavior_count={len(behavior_ref_ids)}"
        )

        # Fetch specific behaviors from Behavior Resolution Service
        logger.info(
            f"🌐 Calling Behavior Resolution Service for behaviors: {behavior_ref_ids}..."
        )
        behaviors = await self._fetch_behaviors_by_ids(user_id, behavior_ref_ids)
        if not behaviors:
            logger.warning(
                f"No behaviors found for IDs {behavior_ref_ids}, "
                f"skipping drift fallback"
            )
            return

        # Hand off to orchestrator in DRIFT_FALLBACK mode
        orchestrator = self._get_orchestrator()
        result = await orchestrator.process(
            user_id=user_id,
            mode="DRIFT_FALLBACK",
            extracted_behavior=behaviors,
            trigger_event_id=drift_event_id
        )

        logger.info(
            f"Drift fallback result for user {user_id}: "
            f"status={result.get('status')}, "
            f"profile={result.get('assigned_profile_id')}"
        )

    async def _fetch_behaviors_by_ids(
        self,
        user_id: str,
        behavior_ids: List[str]
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch specific behaviors by IDs from Behavior Resolution Service.
        
        Calls the Behavior Resolution Service API to retrieve behaviors
        that triggered the drift detection.
        
        Args:
            user_id: UUID of the user
            behavior_ids: List of behavior reference IDs (e.g., ["beh_r_001", "beh_r_002"])
            
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
            f"/api/behaviors/by-ids"
        )
        payload = {
            "user_id": user_id,
            "behavior_ids": behavior_ids
        }

        try:
            logger.info(f"📡 API Call: POST {url} for user {user_id} with {len(behavior_ids)} behavior IDs")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # Handle both response formats: list directly or dict with "behaviors" key
                if isinstance(data, list):
                    behaviors = data
                else:
                    behaviors = data.get("behaviors", [])
                    
                logger.info(
                    f"✅ API Response: Successfully fetched {len(behaviors)} behaviors by IDs"
                )
                return behaviors
                
        except httpx.TimeoutException:
            logger.error(
                f"Timeout fetching behaviors by IDs "
                f"from {settings.BEHAVIOR_RESOLUTION_BASE_URL}"
            )
            return None
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error fetching behaviors by IDs: "
                f"{e.response.status_code} - {e.response.text}"
            )
            return None
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to fetch behaviors by IDs: {e}"
            )
            return None

    async def _fetch_recent_behaviors(
        self, 
        user_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch recent behavior signals from Behavior Resolution Service.
        
        Calls the Behavior Resolution Service API to retrieve the last N
        profile_signals payloads for the user.
        
        DEPRECATED: This method is kept for backward compatibility.
        New drift events should use behavior_ref_ids and _fetch_behaviors_by_ids.
        
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
            logger.info(f"📡 API Call: GET {url}?limit={params['limit']}")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Handle both response formats: list directly or dict with "behaviors" key
                if isinstance(data, list):
                    behaviors = data
                else:
                    behaviors = data.get("behaviors", [])
                    
                logger.info(
                    f"✅ API Response: Successfully fetched {len(behaviors)} recent behaviors for user {user_id}"
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
