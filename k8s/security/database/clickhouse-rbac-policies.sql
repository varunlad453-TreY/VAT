-- ==============================================================================
-- ClickHouse 24.3 SQL-Driven RBAC, Row-Level Policies & Query Quotas
-- Hardening Time-Series Telemetry Ingestion & Analytics
-- ==============================================================================

-- 1. Create Dedicated RBAC Roles
CREATE ROLE IF NOT EXISTS vat_telemetry_writer;
CREATE ROLE IF NOT EXISTS vat_telemetry_reader;

-- 2. Principle of Least Privilege: Table Permissions
-- Writer: Ingestion agent (Vector / Redpanda Kafka Engine) - INSERT ONLY
GRANT INSERT ON vat_telemetry.* TO vat_telemetry_writer;

-- Reader: API Analytics & NOC Console - SELECT ONLY
GRANT SELECT ON vat_telemetry.* TO vat_telemetry_reader;

-- 3. ClickHouse Row-Level Security Policies
-- Isolates telemetry rows so tenants only view their own device logs
CREATE ROW POLICY IF NOT EXISTS tenant_device_policy ON vat_telemetry.telemetry_events
    FOR SELECT
    USING tenant_id = current_user()
    AS RESTRICTIVE
    TO vat_telemetry_reader;

-- 4. Resource Consumption Quotas (Denial-of-Service Protection)
-- Prevents runaway analytical queries from starving real-time ingestion
CREATE QUOTA IF NOT EXISTS vat_analytics_quota
    KEYED BY user_name
    FOR INTERVAL 1 MINUTE
        MAX QUERIES = 120,
        MAX QUERY TIME = 30,
        MAX EXECUTION TIME = 10,
        MAX MEMORY USAGE = 2147483648  -- 2 GiB RAM cap per analytical query
    TO vat_telemetry_reader;

-- 5. Revoke Unauthenticated Default User Access
-- Ensure no unauthenticated or empty-password connections are permitted
ALTER USER default IDENTIFIED WITH sha256_hash BY '0000000000000000000000000000000000000000000000000000000000000000';
REVOKE ALL ON *.* FROM default;
