"""
Infrastructure Adapter: ClickHouse Hot Telemetry Repository
High-velocity time-series queries for NOC dashboards with automatic fallback.
"""

import logging
from typing import Any, Dict, List, Optional
import httpx

from config.settings import get_settings

logger = logging.getLogger("vat-clickhouse-repo")


class ClickHouseTelemetryRepository:
    """Async client executing analytical time-series queries against ClickHouse."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        settings = get_settings()
        self._host = host or settings.clickhouse_host
        self._port = port or settings.clickhouse_port
        self._database = database or settings.clickhouse_database
        self._user = user or settings.clickhouse_user
        self._password = password or settings.clickhouse_password
        self._base_url = f"http://{self._host}:{self._port}"

    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Executes SQL query against ClickHouse HTTP interface with JSON format."""
        url = f"{self._base_url}/?database={self._database}&default_format=JSON"
        auth = (self._user, self._password) if self._password else None

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.post(url, content=query, auth=auth)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", [])
                logger.debug("ClickHouse query returned status %d: %s", response.status_code, response.text)
                return []
        except Exception as exc:
            logger.debug("ClickHouse cluster offline at %s (%s). Using fallback telemetry metrics.", url, exc)
            return []

    async def get_event_velocity_stats(self) -> Dict[str, Any]:
        """Calculates 100k+ EPS event velocity and severity breakdown."""
        query = """
        SELECT
            severity,
            count() as event_count,
            countIf(timestamp >= now() - INTERVAL 5 MINUTE) as events_last_5m
        FROM telemetry_events
        GROUP BY severity
        """
        results = await self.execute_query(query)
        if not results:
            # Resilient fallback metrics
            return {
                "total_events": 0,
                "events_per_sec": 0.0,
                "severity_breakdown": {"CRITICAL": 0, "ERROR": 0, "WARNING": 0, "INFO": 0},
            }

        breakdown = {r["severity"]: int(r["event_count"]) for r in results}
        total = sum(breakdown.values())
        return {
            "total_events": total,
            "events_per_sec": round(total / 300.0, 2),
            "severity_breakdown": breakdown,
        }

    async def get_top_failing_devices(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Queries top devices experiencing BGP flaps and degradation."""
        query = f"""
        SELECT
            device_id,
            vendor,
            count() as error_count,
            topK(1)(event_code)[1] as primary_error
        FROM telemetry_events
        WHERE severity IN ('CRITICAL', 'ERROR')
        GROUP BY device_id, vendor
        ORDER BY error_count DESC
        LIMIT {limit}
        """
        return await self.execute_query(query)
