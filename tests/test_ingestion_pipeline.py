"""
Unit and Integration Tests for Phase 2 (Ingestion Decoupling: Vector.dev & Redpanda)
Validates Vector.dev VRL transformation rules and Redpanda async consumer resilience.
"""

import asyncio
from pathlib import Path
import pytest

from backend.infrastructure.streaming.redpanda_consumer import RedpandaTelemetryConsumer
from backend.infrastructure.cache.redis_service import RedisCacheService


@pytest.mark.asyncio
async def test_redpanda_consumer_lifecycle():
    """Validates consumer startup, state tracking, and graceful shutdown."""
    cache = RedisCacheService()
    consumer = RedpandaTelemetryConsumer(
        bootstrap_servers="localhost:9092",
        topic="vat.telemetry.parsed",
        cache_service=cache,
    )

    assert not consumer.is_running
    await consumer.start()
    assert consumer.is_running

    # Simulate message handling
    sample_event = {
        "raw_log": "%BGP-5-ADJCHANGE: neighbor 10.10.10.1 Down",
        "vendor": "cisco",
        "protocol": "bgp",
        "severity": "CRITICAL",
        "device_id": "Edge-Router-01",
    }
    await consumer._handle_message(sample_event)
    assert consumer.processed_event_count == 1

    await consumer.stop()
    assert not consumer.is_running


def test_vector_config_exists_and_valid():
    """Validates Vector.dev edge configuration structure."""
    config_path = Path("g:/VAT/config/vector/vector.yaml")
    assert config_path.exists(), "vector.yaml must exist in config/vector/"

    content = config_path.read_text(encoding="utf-8")
    assert "syslog_udp" in content
    assert "syslog_tcp" in content
    assert "vat.telemetry.raw" in content
    assert "vat.telemetry.parsed" in content
    assert "normalize_telemetry" in content
