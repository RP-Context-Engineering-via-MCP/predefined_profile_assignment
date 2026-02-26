"""Profile Assignment Event Publisher.

Publishes profile.assigned events to Redis Stream when a user is
successfully assigned to a predefined profile. Downstream consumers
(LLM Orchestration, Recommendation Engine, Analytics) subscribe to
this stream to react to profile assignments.
"""

import json
import time
import logging
import redis.asyncio as aioredis
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

STREAM_NAME = "profile.assigned"


class ProfilePublisher:
    """Publishes profile assignment events to Redis Stream.
    
    Manages Redis connection and publishes structured events when
    users are assigned to predefined profiles (either via cold start
    or drift fallback).
    
    Attributes:
        _redis: Async Redis client connection (lazy initialized)
    """

    def __init__(self):
        """Initialize publisher with no active connection.
        
        Connection is established lazily on first publish.
        """
        self._redis: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        """Get or create Redis connection.
        
        Lazily initializes Redis connection on first use.
        
        Returns:
            aioredis.Redis: Active Redis client connection.
        """
        if self._redis is None:
            self._redis = await aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
        return self._redis

    async def publish(
        self,
        user_id: str,
        assigned_profile_id: str,
        confidence_level: str,
        mode: str,
        trigger_event_id: Optional[str] = None
    ) -> str:
        """Publish a profile.assigned event to Redis Stream.
        
        Emits an event when a user is successfully assigned to a
        predefined profile. This notifies downstream services to
        update their behavior based on the new profile assignment.
        
        Args:
            user_id: UUID of the user being assigned
            assigned_profile_id: Profile code (P1-P6) assigned to user
            confidence_level: Assignment confidence (HIGH, MEDIUM, LOW)
            mode: Assignment mode (COLD_START or DRIFT_FALLBACK)
            trigger_event_id: Drift event ID if mode is DRIFT_FALLBACK
            
        Returns:
            str: Redis Stream message ID of the published event
            
        Event shape published:
            {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "assigned_profile_id": "P3",
                "confidence_level": "HIGH",
                "mode": "COLD_START",
                "trigger_event_id": null,
                "assigned_at": 1740567890
            }
        """
        redis = await self._get_redis()

        payload = {
            "user_id": user_id,
            "assigned_profile_id": assigned_profile_id,
            "confidence_level": confidence_level,
            "mode": mode,
            "trigger_event_id": trigger_event_id or "",
            "assigned_at": int(time.time())
        }

        try:
            message_id = await redis.xadd(
                STREAM_NAME,
                {"payload": json.dumps(payload)}
            )
            logger.info(
                f"Published profile.assigned event: user={user_id}, "
                f"profile={assigned_profile_id}, mode={mode}, "
                f"message_id={message_id}"
            )
            return message_id
        except Exception as e:
            logger.error(
                f"Failed to publish profile.assigned event for user {user_id}: {e}"
            )
            raise

    async def close(self):
        """Close Redis connection.
        
        Should be called during application shutdown to clean up resources.
        """
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
            logger.info("ProfilePublisher Redis connection closed")
