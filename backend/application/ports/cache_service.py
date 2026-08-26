"""
Port Interface: Distributed Cache & Telemetry Event Bus
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class ICacheService(ABC):
    """Abstract port for distributed caching and WebSocket real-time pub/sub."""

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Get cached string value."""
        pass

    @abstractmethod
    async def set(self, key: str, value: str, ttl_seconds: int = 300) -> bool:
        """Set cached key with TTL."""
        pass

    @abstractmethod
    async def publish(self, channel: str, message: Any) -> int:
        """Publish real-time telemetry event to channel subscribers."""
        pass

    @abstractmethod
    async def is_healthy(self) -> bool:
        """Check if cache service is reachable."""
        pass
