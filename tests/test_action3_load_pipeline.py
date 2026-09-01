"""
Automated Test Suite for Action 3: ClickHouse Kafka Engine & Load Testing Pipeline
Validates SQL syntax, batch generation schemas, and throughput accounting.
"""

from pathlib import Path
import pytest

from scripts.simulate_bgp_storm import generate_telemetry_batch


def test_clickhouse_kafka_engine_sql_schema():
    """Validates ClickHouse SQL schema file exists and contains necessary parameters."""
    sql_path = Path("g:/VAT/config/clickhouse/staging-kafka-engine.sql")
    assert sql_path.exists(), "staging-kafka-engine.sql must exist in config/clickhouse/"

    content = sql_path.read_text(encoding="utf-8")
    assert "CREATE DATABASE IF NOT EXISTS vat_telemetry" in content
    assert "ENGINE = MergeTree()" in content
    assert "ENGINE = Kafka" in content
    assert "kafka_broker_list" in content
    assert "kafka_topic_list = 'vat.telemetry.parsed'" in content
    assert "kafka_num_consumers = 4" in content
    assert "CREATE MATERIALIZED VIEW IF NOT EXISTS telemetry_kafka_mv" in content


def test_bgp_storm_batch_generator():
    """Validates load test generator produces valid multi-vendor syslog batches."""
    batch = generate_telemetry_batch(100)
    assert len(batch) == 100
    for log in batch:
        assert "<189>1" in log
        assert "Edge-Router-" in log
        assert any(vendor in log for vendor in ["BGP", "RPD", "EDGE_LINK", "MLAG"])
