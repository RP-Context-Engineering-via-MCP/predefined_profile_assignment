"""Consumer layer for inbound Redis Stream events.

This module provides consumers for processing events from upstream services
via Redis Streams, specifically handling drift events from the Drift Detection Service.
"""

from app.consumer.redis_consumer import DriftEventConsumer
from app.consumer.drift_event_handler import DriftEventHandler

__all__ = ["DriftEventConsumer", "DriftEventHandler"]
