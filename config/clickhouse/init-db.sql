-- ==============================================================================
-- ClickHouse Schema: Hot Telemetry Time-Series Database
-- Target Scale: 100,000+ EPS • 90% Compression • Sub-Second NOC Aggregations
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS vat_telemetry;

USE vat_telemetry;

-- 1. Main Compressed Time-Series Storage Table
CREATE TABLE IF NOT EXISTS telemetry_events (
    timestamp DateTime64(3, 'UTC') DEFAULT now64(3),
    received_at DateTime64(3, 'UTC') DEFAULT now64(3),
    device_id LowCardinality(String),
    vendor LowCardinality(String),
    protocol LowCardinality(String),
    severity LowCardinality(String),
    category LowCardinality(String),
    event_code LowCardinality(String),
    interface String,
    peer_ip String,
    raw_log String,
    ingest_node LowCardinality(String)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (vendor, protocol, severity, device_id, timestamp)
SETTINGS index_granularity = 8192;

-- 2. Kafka Engine Table (Subscribes to Redpanda topic: vat.telemetry.parsed)
CREATE TABLE IF NOT EXISTS telemetry_kafka_queue (
    timestamp DateTime64(3, 'UTC'),
    received_at DateTime64(3, 'UTC'),
    device_id String,
    vendor String,
    protocol String,
    severity String,
    category String,
    event_code String,
    interface String,
    peer_ip String,
    raw_log String,
    ingest_node String
)
ENGINE = Kafka
SETTINGS
    kafka_broker_list = 'vat-redpanda-service.vat-system.svc.cluster.local:9092',
    kafka_topic_list = 'vat.telemetry.parsed',
    kafka_group_name = 'clickhouse-telemetry-sink-group',
    kafka_format = 'JSONEachRow',
    kafka_num_consumers = 2;

-- 3. Materialized View: Pipes streaming Kafka events into MergeTree table
CREATE MATERIALIZED VIEW IF NOT EXISTS telemetry_kafka_mv TO telemetry_events AS
SELECT * FROM telemetry_kafka_queue;
