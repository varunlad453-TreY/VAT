"""
Unit and Integration Tests for Phase 3 (Polyglot Persistence: ClickHouse & Qdrant)
Validates ClickHouse analytical queries and Qdrant distributed vector search with fallback.
"""

import pytest
from backend.infrastructure.repositories.clickhouse_telemetry_repository import (
    ClickHouseTelemetryRepository,
)
from backend.infrastructure.repositories.qdrant_vector_repository import (
    QdrantVectorRepository,
)


@pytest.mark.asyncio
async def test_clickhouse_telemetry_repository_fallback():
    """Validates ClickHouse repository returns structured stats on offline fallback."""
    repo = ClickHouseTelemetryRepository(host="localhost", port=8123)

    stats = await repo.get_event_velocity_stats()
    assert "total_events" in stats
    assert "events_per_sec" in stats
    assert "severity_breakdown" in stats

    top_devices = await repo.get_top_failing_devices(limit=5)
    assert isinstance(top_devices, list)


@pytest.mark.asyncio
async def test_qdrant_vector_repository_search_fallback():
    """Validates Qdrant repository queries with HNSW fallback to verified TAC corpus."""
    repo = QdrantVectorRepository(host="localhost", port=6333)

    docs = await repo.find_relevant_docs(
        query_text="BGP hold timer expired peer 10.10.10.1 down",
        limit=3,
        vendor="cisco",
        protocol="bgp",
    )

    assert len(docs) > 0
    assert "title" in docs[0]
    assert "chunk_text" in docs[0]
    assert docs[0]["vendor"] == "cisco"
