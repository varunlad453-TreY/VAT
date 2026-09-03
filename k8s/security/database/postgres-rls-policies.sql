-- ==============================================================================
-- PostgreSQL 16 Kernel-Level Row-Level Security (RLS) & RBAC Hardening
-- Multi-Tenant Isolation & Least-Privilege Role Provisioning
-- ==============================================================================

-- 1. Create Base Functional Roles
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vat_app_role') THEN
        CREATE ROLE vat_app_role NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vat_readonly_role') THEN
        CREATE ROLE vat_readonly_role NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vat_migrator_role') THEN
        CREATE ROLE vat_migrator_role NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
    END IF;
END $$;

-- 2. Grant Table-Level Privileges to Roles
GRANT USAGE ON SCHEMA public TO vat_app_role, vat_readonly_role, vat_migrator_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO vat_app_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO vat_app_role;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO vat_readonly_role;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO vat_migrator_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO vat_migrator_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO vat_app_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO vat_app_role;

-- 3. Enable & FORCE Row-Level Security on Core Enterprise Tables
-- FORCE ensures that table owners cannot accidentally bypass RLS policies
ALTER TABLE IF EXISTS documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS documents FORCE ROW LEVEL SECURITY;

ALTER TABLE IF EXISTS chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS chunks FORCE ROW LEVEL SECURITY;

ALTER TABLE IF EXISTS queries ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS queries FORCE ROW LEVEL SECURITY;

ALTER TABLE IF EXISTS audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS audit_logs FORCE ROW LEVEL SECURITY;

-- 4. Multi-Tenant Session-Context Isolation Policies
-- Evaluates session variable 'app.current_tenant' set via asyncpg connection setup
DROP POLICY IF EXISTS tenant_isolation_documents ON documents;
CREATE POLICY tenant_isolation_documents ON documents
    AS RESTRICTIVE
    FOR ALL
    TO vat_app_role, vat_readonly_role
    USING (
        tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::varchar
    )
    WITH CHECK (
        tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::varchar
    );

DROP POLICY IF EXISTS tenant_isolation_chunks ON chunks;
CREATE POLICY tenant_isolation_chunks ON chunks
    AS RESTRICTIVE
    FOR ALL
    TO vat_app_role, vat_readonly_role
    USING (
        tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::varchar
    )
    WITH CHECK (
        tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::varchar
    );

DROP POLICY IF EXISTS tenant_isolation_queries ON queries;
CREATE POLICY tenant_isolation_queries ON queries
    AS RESTRICTIVE
    FOR ALL
    TO vat_app_role, vat_readonly_role
    USING (
        tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::varchar
    )
    WITH CHECK (
        tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::varchar
    );

-- 5. Vault Database Secret Engine Integration Template
-- Vault's dynamic secret engine executes this creation statement upon pod authentication:
/*
CREATE ROLE "{{name}}" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}' INHERIT;
GRANT vat_app_role TO "{{name}}";
ALTER ROLE "{{name}}" SET search_path = public;
*/
