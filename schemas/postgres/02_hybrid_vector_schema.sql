-- ============================================================================
-- Enterprise Multi-Vendor Hybrid Vector & Audit Schema (VAT Phase 2)
-- ============================================================================

-- Ensure pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Ensure vendor_knowledge table exists
CREATE TABLE IF NOT EXISTS vendor_knowledge (
    id SERIAL PRIMARY KEY,
    source_url TEXT NOT NULL,
    title TEXT,
    vendor VARCHAR(64) NOT NULL DEFAULT 'cisco',
    product_family VARCHAR(64) DEFAULT 'routing',
    protocol VARCHAR(32) DEFAULT 'ospf',
    error_codes TEXT[] DEFAULT '{}',
    chunk_text TEXT NOT NULL,
    embedding vector(384),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add Phase 2 columns if not already present
ALTER TABLE vendor_knowledge 
    ADD COLUMN IF NOT EXISTS product_family VARCHAR(64) DEFAULT 'routing',
    ADD COLUMN IF NOT EXISTS protocol VARCHAR(32) DEFAULT 'ospf',
    ADD COLUMN IF NOT EXISTS error_codes TEXT[] DEFAULT '{}';

-- Create or update full-text search tsvector column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'vendor_knowledge' AND column_name = 'tsv_content'
    ) THEN
        ALTER TABLE vendor_knowledge 
            ADD COLUMN tsv_content tsvector 
            GENERATED ALWAYS AS (to_tsvector('english', coalesce(title, '') || ' ' || coalesce(vendor, '') || ' ' || coalesce(protocol, '') || ' ' || chunk_text)) STORED;
    END IF;
END $$;

-- Indexes for Dense & Sparse Hybrid Retrieval
CREATE INDEX IF NOT EXISTS idx_vendor_knowledge_embedding 
    ON vendor_knowledge USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_vendor_knowledge_tsv 
    ON vendor_knowledge USING gin(tsv_content);

CREATE INDEX IF NOT EXISTS idx_vendor_knowledge_vendor_proto 
    ON vendor_knowledge(vendor, protocol);

-- ============================================================================
-- Permanent Troubleshooting & Remediation Audit Ledger Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS troubleshooting_audit_ledger (
    id SERIAL PRIMARY KEY,
    incident_id VARCHAR(64),
    device_id VARCHAR(128) NOT NULL,
    vendor VARCHAR(32) NOT NULL,
    raw_logs TEXT NOT NULL,
    diagnosis TEXT NOT NULL,
    root_cause TEXT NOT NULL,
    risk_level VARCHAR(16) NOT NULL,
    remediation_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    rollback_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    cited_sources JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence_score REAL NOT NULL DEFAULT 0.90,
    model_used VARCHAR(64) DEFAULT 'deterministic-rag-synthesizer',
    executed_by VARCHAR(64) DEFAULT 'noc_operator',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_ledger_device_vendor 
    ON troubleshooting_audit_ledger(device_id, vendor);

CREATE INDEX IF NOT EXISTS idx_audit_ledger_created_at 
    ON troubleshooting_audit_ledger(created_at DESC);
