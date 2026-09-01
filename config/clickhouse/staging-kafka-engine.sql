-- ==============================================================================
-- Action 3: ClickHouse Kafka Table Engine & High-Throughput Materialized View
-- Target Throughput: 100,000+ EPS • 4 Consumers • Micro-Batch Granularity (65k)
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS vat_telemetry;

USE vat_telemetry;

-- 1. Main Columnar Storage Table (MergeTree with LZ4 / ZSTD Compression)
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
SETTINGS 
    index_granularity = 8192,
    min_bytes_for_wide_part = 10485760,
    min_rows_for_wide_part = 50000;

-- 2. Kafka Engine Queue Table (Consumes from Redpanda: vat.telemetry.parsed)
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
    kafka_broker_list = 'vat-redpanda-staging-service.vat-staging.svc.cluster.local:9092',
    kafka_topic_list = 'vat.telemetry.parsed',
    kafka_group_name = 'clickhouse-staging-consumer-group',
    kafka_format = 'JSONEachRow',
    kafka_num_consumers = 4,
    kafka_max_block_size = 65536,
    kafka_poll_timeout_ms = 500,
    kafka_flush_interval_ms = 1000;

-- 3. Materialized View (High-Speed Ingestion Pipeline)
CREATE MATERIALIZED VIEW IF NOT EXISTS telemetry_kafka_mv TO telemetry_events AS
SELECT 
    assumeNotNull(timestamp) AS timestamp,
    assumeNotNull(received_at) AS received_at,
    device_id,
    vendor,
    protocol,
    severity,
    category,
    event_code,
    interface,
    peer_ip,
    raw_log,
    ingest_node
FROM telemetry_kafka_queue;
