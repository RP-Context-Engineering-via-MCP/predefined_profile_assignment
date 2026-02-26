"""Redis Stream Consumer for Drift Events.

Consumes drift.events stream from the Drift Detection Service using
Redis consumer groups for reliable message processing. Runs as a
background asyncio task alongside the FastAPI HTTP server.
"""

import asyncio
import json
import logging
import redis.asyncio as aioredis
from typing import Optional
from app.consumer.drift_event_handler import DriftEventHandler
from app.core.config import settings

logger = logging.getLogger(__name__)

STREAM_NAME = "drift.events"
GROUP_NAME = "predefined-profile-service"
CONSUMER_NAME = "profile-worker-1"
BLOCK_MS = 5000      # Block 5 seconds waiting for messages
MAX_MESSAGES = 10    # Read up to 10 messages at a time


class DriftEventConsumer:
    """Consumes drift events from Redis Stream.
    
    Uses Redis consumer groups for reliable, exactly-once message processing.
    Failed messages remain in the Pending Entries List (PEL) for retry.
    
    Attributes:
        _running: Flag to control consumer loop lifecycle
        _redis: Async Redis client connection
        _handler: DriftEventHandler for processing events
    """

    def __init__(self):
        """Initialize consumer with no active connection.
        
        Connection is established when start() is called.
        """
        self._running: bool = False
        self._redis: Optional[aioredis.Redis] = None
        self._handler = DriftEventHandler()

    async def start(self):
        """Start the consumer loop.
        
        Connects to Redis, ensures consumer group exists, and begins
        reading messages from the drift.events stream. Runs until
        stop() is called.
        
        The consumer loop:
        1. Blocks waiting for new messages (up to BLOCK_MS)
        2. Processes each message via DriftEventHandler
        3. Acknowledges successfully processed messages
        4. Leaves failed messages in PEL for retry
        """
        logger.info(f"Starting DriftEventConsumer for stream: {STREAM_NAME}")
        
        self._redis = await aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        await self._ensure_consumer_group()
        self._running = True

        while self._running:
            try:
                messages = await self._redis.xreadgroup(
                    groupname=GROUP_NAME,
                    consumername=CONSUMER_NAME,
                    streams={STREAM_NAME: ">"},
                    count=MAX_MESSAGES,
                    block=BLOCK_MS
                )
                
                if messages:
                    logger.info(f"Received {sum(len(entries) for _, entries in messages)} message(s) from {STREAM_NAME}")
                    for stream_name, entries in messages:
                        for entry_id, data in entries:
                            logger.info(f"📥 Consuming event: stream={stream_name}, entry_id={entry_id}")
                            await self._process(entry_id, data)

            except asyncio.CancelledError:
                logger.info("DriftEventConsumer received cancellation signal")
                break
            except Exception as e:
                logger.error(f"DriftEventConsumer error: {e}")
                await asyncio.sleep(2)  # Backoff before retry

        logger.info("DriftEventConsumer stopped")

    async def _process(self, entry_id: str, data: dict):
        """Process a single drift event message.
        
        Parses the message payload and delegates to DriftEventHandler.
        Only acknowledges the message if processing succeeds.
        
        Args:
            entry_id: Redis Stream message ID
            data: Message data dict containing 'payload' key
        """
        try:
            payload_str = data.get("payload", "{}")
            event_payload = json.loads(payload_str)
            
            logger.info(f"🔄 Processing drift event: {entry_id}, payload={event_payload}")
            await self._handler.handle(event_payload)
            
            # Acknowledge successful processing
            await self._redis.xack(STREAM_NAME, GROUP_NAME, entry_id)
            logger.debug(f"Acknowledged drift event: {entry_id}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in drift event {entry_id}: {e}")
            # Ack malformed messages to prevent infinite retry
            await self._redis.xack(STREAM_NAME, GROUP_NAME, entry_id)
        except Exception as e:
            logger.error(f"Failed to process drift event {entry_id}: {e}")
            # Do NOT ack - message stays in PEL for retry

    async def _ensure_consumer_group(self):
        """Create consumer group if it doesn't exist.
        
        Uses MKSTREAM to auto-create the stream if needed.
        Silently ignores if group already exists.
        """
        try:
            await self._redis.xgroup_create(
                STREAM_NAME,
                GROUP_NAME,
                id="0",
                mkstream=True
            )
            logger.info(f"Created consumer group: {GROUP_NAME}")
        except aioredis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group already exists: {GROUP_NAME}")
            else:
                raise

    def stop(self):
        """Signal the consumer loop to stop.
        
        Sets the running flag to False. The loop will exit
        after the current blocking read completes.
        """
        logger.info("Stopping DriftEventConsumer...")
        self._running = False

    async def close(self):
        """Close Redis connection.
        
        Should be called during application shutdown.
        """
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
            logger.info("DriftEventConsumer Redis connection closed")
