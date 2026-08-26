"""
Database Client - asyncpg Connection Pool with pgvector support
"""

import logging
from typing import Any, List, Optional
import asyncpg

from config.settings import get_settings

logger = logging.getLogger(__name__)


async def _init_connection(conn: asyncpg.Connection) -> None:
    """Register pgvector types on new asyncpg connection."""
    try:
        from pgvector.asyncpg import register_vector
        await register_vector(conn)
    except Exception as exc:
        logger.debug("pgvector asyncpg codec registration skipped or not installed: %s", exc)


class Database:
    """Async PostgreSQL Database Manager."""

    def __init__(self) -> None:
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self, min_size: int = 2, max_size: int = 10) -> None:
        """Establish connection pool to PostgreSQL."""
        if self.pool is not None:
            return

        settings = get_settings()
        logger.info("Connecting to PostgreSQL at %s:%s/%s...", settings.postgres_host, settings.postgres_port, settings.postgres_database)
        
        try:
            self.pool = await asyncpg.create_pool(
                settings.pg_url,
                min_size=min_size,
                max_size=max_size,
                init=_init_connection,
            )
            logger.info("PostgreSQL connection pool established successfully.")
        except Exception as exc:
            logger.warning("Could not connect to PostgreSQL database: %s", exc)
            self.pool = None

    async def disconnect(self) -> None:
        """Close connection pool."""
        if self.pool is None:
            return
        await self.pool.close()
        self.pool = None
        logger.info("PostgreSQL connection pool closed.")

    async def is_connected(self) -> bool:
        """Check if database pool is active."""
        if self.pool is None:
            return False
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchval("SELECT 1") == 1
        except Exception:
            return False

    async def fetch(self, query: str, *args: Any) -> List[asyncpg.Record]:
        """Fetch multiple rows."""
        if self.pool is None:
            raise ConnectionError("Database connection pool is not initialized")
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> Optional[asyncpg.Record]:
        """Fetch a single row."""
        if self.pool is None:
            raise ConnectionError("Database connection pool is not initialized")
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        """Fetch a single scalar value."""
        if self.pool is None:
            raise ConnectionError("Database connection pool is not initialized")
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def execute(self, query: str, *args: Any) -> str:
        """Execute a query without returning rows."""
        if self.pool is None:
            raise ConnectionError("Database connection pool is not initialized")
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def executemany(self, query: str, args: List[Any]) -> None:
        """Execute a query across a batch of arguments."""
        if self.pool is None:
            raise ConnectionError("Database connection pool is not initialized")
        async with self.pool.acquire() as conn:
            await conn.executemany(query, args)


# Global singleton instance
db = Database()
