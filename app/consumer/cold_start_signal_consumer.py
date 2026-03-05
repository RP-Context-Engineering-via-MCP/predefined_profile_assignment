"""Redis Stream Consumer for Cold Start Profile Signal Events.

Consumes behaviour.event stream (profile_signals.extracted event type) from the 
Behavior Extraction Service using Redis consumer groups for reliable message processing. 
Runs as a background asyncio task alongside the FastAPI HTTP server.
"""

import asyncio
import json
import logging
import redis.asyncio as aioredis
from typing import Optional
from app.consumer.cold_start_signal_handler import ColdStartSignalHandler
from app.core.config import settings

logger = logging.getLogger(__name__)

EVENT_TYPE = "profile_signals.extracted"
CONSUMER_NAME = "profile-signal-worker-1"
BLOCK_MS = 5000      # Block 5 seconds waiting for messages
MAX_MESSAGES = 10    # Read up to 10 messages at a time


class ColdStartSignalConsumer:
    """Consumes cold start profile signal events from Redis Stream.
    
    Uses Redis consumer groups for reliable, exactly-once message processing.
    Failed messages remain in the Pending Entries List (PEL) for retry.
    
    Attributes:
        _running: Flag to control consumer loop lifecycle
        _redis: Async Redis client connection
        _handler: ColdStartSignalHandler for processing events
    """

    def __init__(self):
        """Initialize consumer with no active connection.
        
        Connection is established when start() is called.
        """
        self._running: bool = False
        self._redis: Optional[aioredis.Redis] = None
        self._handler = ColdStartSignalHandler()

    async def start(self):
        """Start the consumer loop.
        
        Connects to Redis, ensures consumer group exists, and begins
        reading messages from the behaviour.event stream. Filters for 
        profile_signals.extracted event type. Runs until stop() is called.
        
        The consumer loop:
        1. Blocks waiting for new messages (up to BLOCK_MS)
        2. Filters messages by event_type = profile_signals.extracted
        3. Processes matching messages via ColdStartSignalHandler
        4. Acknowledges successfully processed messages
        5. Leaves failed messages in PEL for retry
        """
        logger.info(f"Starting ColdStartSignalConsumer for stream: {settings.BEHAVIOUR_STREAM_NAME}, event_type: {EVENT_TYPE}")
        
        self._redis = await aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        await self._ensure_consumer_group()
        self._running = True

        while self._running:
            try:
                messages = await self._redis.xreadgroup(
                    groupname=settings.PROFILE_SERVICE_CONSUMER_GROUP,
                    consumername=CONSUMER_NAME,
                    streams={settings.BEHAVIOUR_STREAM_NAME: ">"},
                    count=MAX_MESSAGES,
                    block=BLOCK_MS
                )
                
                if messages:
                    logger.info(f"Received {sum(len(entries) for _, entries in messages)} message(s) from {settings.BEHAVIOUR_STREAM_NAME}")
                    for stream_name, entries in messages:
                        for entry_id, data in entries:
                            logger.info(f"📥 Consuming event: stream={stream_name}, entry_id={entry_id}")
                            await self._process(entry_id, data)

            except asyncio.CancelledError:
                logger.info("ColdStartSignalConsumer received cancellation signal")
                break
            except Exception as e:
                logger.error(f"ColdStartSignalConsumer error: {e}")
                await asyncio.sleep(2)  # Backoff before retry

        logger.info("ColdStartSignalConsumer stopped")

    async def _process(self, entry_id: str, data: dict):
        """Process a single cold start signal event message.
        
        Parses the message payload, filters by event_type, and delegates to 
        ColdStartSignalHandler. Only acknowledges the message if processing succeeds.
        
        Args:
            entry_id: Redis Stream message ID
            data: Message data dict containing 'payload' and 'event_type' keys
        """
        try:
            # Check event type filter
            event_type = data.get("event_type", "")
            if event_type != EVENT_TYPE:
                logger.debug(f"Skipping event {entry_id}: event_type={event_type} (expected {EVENT_TYPE})")
                # Acknowledge events we're not interested in
                await self._redis.xack(settings.BEHAVIOUR_STREAM_NAME, settings.PROFILE_SERVICE_CONSUMER_GROUP, entry_id)
                return
            
            payload_str = data.get("payload", "{}")
            event_payload = json.loads(payload_str)
            
            logger.info(f"🔄 Processing cold start signal event: {entry_id}, payload={event_payload}")
            await self._handler.handle(event_payload)
            
            # Acknowledge successful processing
            await self._redis.xack(settings.BEHAVIOUR_STREAM_NAME, settings.PROFILE_SERVICE_CONSUMER_GROUP, entry_id)
            logger.debug(f"Acknowledged cold start signal event: {entry_id}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in cold start signal event {entry_id}: {e}")
            # Ack malformed messages to prevent infinite retry
            await self._redis.xack(settings.BEHAVIOUR_STREAM_NAME, settings.PROFILE_SERVICE_CONSUMER_GROUP, entry_id)
        except Exception as e:
            logger.error(f"Failed to process cold start signal event {entry_id}: {e}")
            # Do NOT ack - message stays in PEL for retry

    async def _ensure_consumer_group(self):
        """Create consumer group if it doesn't exist.
        
        Uses MKSTREAM to auto-create the stream if needed.
        Silently ignores if group already exists.
        """
        try:
            await self._redis.xgroup_create(
                settings.BEHAVIOUR_STREAM_NAME,
                settings.PROFILE_SERVICE_CONSUMER_GROUP,
                id="0",
                mkstream=True
            )
            logger.info(f"Created consumer group: {settings.PROFILE_SERVICE_CONSUMER_GROUP}")
        except aioredis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group already exists: {settings.PROFILE_SERVICE_CONSUMER_GROUP}")
            else:
                raise

    def stop(self):
        """Signal the consumer loop to stop.
        
        Sets the running flag to False. The loop will exit
        after the current blocking read completes.
        """
        logger.info("Stopping ColdStartSignalConsumer...")
        self._running = False

    async def close(self):
        """Close Redis connection.
        
        Should be called during application shutdown.
        """
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
            logger.info("ColdStartSignalConsumer Redis connection closed")
