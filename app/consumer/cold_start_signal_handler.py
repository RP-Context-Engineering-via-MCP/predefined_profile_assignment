"""Cold Start Signal Event Handler.

Processes profile signal extraction events received from the Behavior Extraction Service
when a user is in cold start mode. Listens to behavior.events stream and filters for
profile_signals.extracted event type.
"""

import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class ColdStartSignalHandler:
    """Handles profile signal extraction events for cold start users.
    
    When a user is in cold start mode and their behavior is extracted by the
    Behavior Extraction Service, this handler receives the profile signals
    and triggers profile assignment using the IntakeOrchestrator.
    
    Flow:
    1. Receive event from behavior.events stream (event_type: profile_signals.extracted)
    2. Extract and validate profile signals (intents, interests, signals, etc.)
    3. Pass to IntakeOrchestrator in COLD_START mode
    4. IntakeOrchestrator handles matching, ranking, and potential assignment
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
        """Handle a profile signal extraction event.
        
        Processes profile signal events from the behavior.events Redis Stream
        (event_type: profile_signals.extracted) when a user is in cold start mode.
        
        Args:
            event: Profile signal event dict with shape:
                {
                    "user_id": "user_123",
                    "prompt_id": "segment_abc456",
                    "profile_signals": {
                        "intents": {
                            "LEARNING": 0.8,
                            "TASK_COMPLETION": 0.4
                        },
                        "interests": {
                            "PROGRAMMING": 0.9,
                            "AI": 0.7,
                            "DATA_SCIENCE": 0.5
                        },
                        "behavior_level": "INTERMEDIATE",
                        "signals": {
                            "CODE_FOCUSED": 0.9,
                            "STEP_BY_STEP": 0.6,
                            "DETAILED_EXPLANATION": 0.7
                        },
                        "complexity": 0.7,
                        "consistency": 0.8
                    }
                }
                
                Fields:
                - user_id: Required to identify the user for profile assignment.
                - prompt_id: Traceability ID for logging and correlation.
                - profile_signals: Extracted behavioral signals containing:
                  * intents: Dict of intent types with confidence scores
                  * interests: Dict of interest areas with confidence scores
                  * behavior_level: User's behavioral sophistication level
                  * signals: Dict of behavioral signals with weights
                  * complexity: Overall complexity score (0-1)
                  * consistency: Consistency score (0-1)
        """
        user_id = event.get("user_id")
        prompt_id = event.get("prompt_id")
        profile_signals = event.get("profile_signals")

        if not user_id:
            logger.warning(f"Profile signal event missing user_id, skipping")
            return

        if not profile_signals:
            logger.warning(
                f"Profile signal event for user {user_id} missing profile_signals, skipping"
            )
            return

        logger.info(
            f"✅ Processing cold start signal: user={user_id}, prompt_id={prompt_id}"
        )

        # Validate profile_signals structure
        required_fields = ["intents", "interests", "behavior_level", "signals", "complexity", "consistency"]
        missing_fields = [field for field in required_fields if field not in profile_signals]
        
        if missing_fields:
            logger.warning(
                f"Profile signals for user {user_id} missing required fields: {missing_fields}, "
                f"skipping cold start processing"
            )
            return

        # Log extracted signals summary
        logger.info(
            f"📊 Extracted signals: "
            f"intents={len(profile_signals['intents'])}, "
            f"interests={len(profile_signals['interests'])}, "
            f"behavior_level={profile_signals['behavior_level']}, "
            f"signals={len(profile_signals['signals'])}, "
            f"complexity={profile_signals['complexity']:.2f}, "
            f"consistency={profile_signals['consistency']:.2f}"
        )

        # Hand off to orchestrator in COLD_START mode
        orchestrator = self._get_orchestrator()
        try:
            result = await orchestrator.process(
                user_id=user_id,
                mode="COLD_START",
                extracted_behavior=profile_signals,
                trigger_event_id=prompt_id
            )

            logger.info(
                f"Cold start processing result for user {user_id}: "
                f"status={result.get('status')}, "
                f"profile={result.get('assigned_profile_id')}, "
                f"confidence={result.get('confidence_level')}, "
                f"prompt_count={result.get('prompt_count')}"
            )
        except Exception as e:
            logger.error(
                f"Failed to process cold start signals for user {user_id}: {e}",
                exc_info=True
            )
            raise
