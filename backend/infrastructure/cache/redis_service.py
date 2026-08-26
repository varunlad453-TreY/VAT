"""
Infrastructure Adapter: Redis Cache & Event Bus Service
Distributed caching and real-time WebSocket pub/sub with in-memory fallback.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from backend.application.ports.cache_service import ICacheService

logger = logging.getLogger(__name__)


class RedisCacheService(ICacheService):
    """Redis Cache & Telemetry Event Bus with automatic in-memory fallback."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        self._redis_url = redis_url
        self._client: Optional[Any] = None
        self._connection_attempted = False
        self._in_memory_cache: Dict[str, Tuple[str, float]] = {}  # key -> (value, expire_timestamp)
        self._in_memory_subscribers: Dict[str, List[Any]] = {}

    async def _get_client(self) -> Optional[Any]:
        """Lazy connection to Redis server."""
        if not self._connection_attempted:
            self._connection_attempted = True
            try:
                import redis.asyncio as aioredis
                client = aioredis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=1.0,
                )
                await client.ping()
                self._client = client
                logger.info("Redis cache client connected at %s", self._redis_url)
            except Exception as exc:
                logger.debug("Redis connection skipped or offline (%s). Using in-memory cache fallback.", exc)
                self._client = None
        return self._client

    async def get(self, key: str) -> Optional[str]:
        """Get cached string value."""
        client = await self._get_client()
        if client is not None:
            try:
                return await client.get(key)
            except Exception as exc:
                logger.debug("Redis get error: %s", exc)

        # In-memory fallback
        import time
        if key in self._in_memory_cache:
            val, expiry = self._in_memory_cache[key]
            if expiry == 0 or expiry > time.time():
                return val
            else:
                del self._in_memory_cache[key]
        return None

    async def set(self, key: str, value: str, ttl_seconds: int = 300) -> bool:
        """Set cached key with TTL."""
        client = await self._get_client()
        if client is not None:
            try:
                await client.set(key, value, ex=ttl_seconds)
                return True
            except Exception as exc:
                logger.debug("Redis set error: %s", exc)

        # In-memory fallback
        import time
        expiry = (time.time() + ttl_seconds) if ttl_seconds > 0 else 0
        self._in_memory_cache[key] = (value, expiry)
        return True

    async def publish(self, channel: str, message: Any) -> int:
        """Publish real-time telemetry event to channel subscribers."""
        msg_str = json.dumps(message) if not isinstance(message, str) else message

        client = await self._get_client()
        if client is not None:
            try:
                return await client.publish(channel, msg_str)
            except Exception as exc:
                logger.debug("Redis publish error: %s", exc)

        # In-memory notification dispatch
        subs = self._in_memory_subscribers.get(channel, [])
        for sub in subs:
            try:
                if callable(sub):
                    sub(msg_str)
            except Exception:
                pass
        return len(subs)

    async def is_healthy(self) -> bool:
        """Check if Redis cache service is reachable."""
        try:
            client = await self._get_client()
            if client is not None:
                return await client.ping()
        except Exception:
            pass
        return False
