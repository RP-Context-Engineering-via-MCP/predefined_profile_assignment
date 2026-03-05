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

        # Validate and transform behaviors to expected format
        validated_behaviors = self._validate_and_transform_behaviors(behaviors)
        if not validated_behaviors:
            logger.warning(
                f"No valid behaviors after validation for user {user_id}, "
                f"skipping drift fallback"
            )
            return

        logger.info(
            f"✅ Validated {len(validated_behaviors)} behaviors for drift fallback processing"
        )

        # Hand off to orchestrator in DRIFT_FALLBACK mode
        orchestrator = self._get_orchestrator()
        result = await orchestrator.process(
            user_id=user_id,
            mode="DRIFT_FALLBACK",
            extracted_behavior=validated_behaviors,
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

    def _validate_and_transform_behaviors(
        self,
        behaviors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate and transform behaviors to expected format.
        
        Ensures each behavior has required fields: intents, interests,
        behavior_level, signals, complexity, and consistency.
        
        If behaviors don't have the expected structure, attempts to extract
        or default the values to prevent processing failures.
        
        Args:
            behaviors: Raw behaviors from Behavior Resolution Service
            
        Returns:
            List of validated/transformed behaviors with required fields.
            Behaviors that cannot be transformed are logged and skipped.
        """
        from app.core.constants import DefaultValues
        
        required_fields = ["intents", "interests", "behavior_level", "signals"]
        validated = []
        
        for idx, behavior in enumerate(behaviors):
            # Log first behavior structure for debugging (only once)
            if idx == 0:
                logger.info(
                    f"📋 Sample behavior structure: keys={list(behavior.keys())[:15]}"
                )
            
            # Check if behavior is already in correct format
            missing_fields = [field for field in required_fields if field not in behavior]
            
            if missing_fields:
                # Log detailed info for the first few failures
                if idx < 3:
                    logger.warning(
                        f"⚠️ Behavior {idx + 1}/{len(behaviors)} missing required fields: {missing_fields}. "
                        f"Available keys: {list(behavior.keys())}"
                    )
                    # Log a sample of the actual content
                    sample_keys = list(behavior.keys())[:5]
                    sample_content = {k: behavior.get(k) for k in sample_keys}
                    logger.warning(f"Sample content: {sample_content}")
                
                # Attempt to construct default behavior structure
                transformed_behavior = self._attempt_behavior_transformation(behavior)
                if transformed_behavior:
                    logger.info(f"✓ Transformed behavior {idx + 1} to expected format")
                    validated.append(transformed_behavior)
                else:
                    logger.warning(f"✗ Skipping behavior {idx + 1} - cannot transform")
                continue
            
            # Ensure optional fields have defaults
            if "complexity" not in behavior:
                behavior["complexity"] = DefaultValues.DEFAULT_COMPLEXITY
            
            if "consistency" not in behavior:
                behavior["consistency"] = DefaultValues.DEFAULT_CONSISTENCY
            
            validated.append(behavior)
        
        logger.info(
            f"Validation complete: {len(validated)}/{len(behaviors)} behaviors valid"
        )
        
        return validated

    def _attempt_behavior_transformation(
        self,
        behavior: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Attempt to transform a raw behavior into expected format.
        
        Tries to extract or default missing fields to salvage behaviors
        that don't match the expected structure from Behavior Resolution Service.
        
        Args:
            behavior: Raw behavior dict
            
        Returns:
            Transformed behavior dict with required fields, or None if transformation fails
        """
        from app.core.constants import DefaultValues
        
        try:
            # Create a new behavior dict with default values
            transformed = {
                "intents": behavior.get("intents", {}),
                "interests": behavior.get("interests", {}),
                "behavior_level": behavior.get("behavior_level", "BASIC"),
                "signals": behavior.get("signals", {}),
                "complexity": behavior.get("complexity", DefaultValues.DEFAULT_COMPLEXITY),
                "consistency": behavior.get("consistency", DefaultValues.DEFAULT_CONSISTENCY)
            }
            
            # Validate that critical fields are not empty
            if not transformed["intents"] and not transformed["interests"]:
                logger.debug("Transformation failed: no intents or interests")
                return None
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error during behavior transformation: {e}")
            return None
