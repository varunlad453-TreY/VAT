"""0001_initial_baseline

Revision ID: 0001_initial_baseline
Revises: None
Create Date: 2026-08-31 21:20:00.000000 UTC

Base migration that safely baselines existing PostgreSQL schemas (vendor_knowledge and
troubleshooting_audit_ledger) with pgvector HNSW indexing, full-text tsvector search,
and audit ledger storage without data loss.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001_initial_baseline'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Baseline vendor_knowledge table
    op.execute("""
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
    """)

    # 3. Add generated tsvector column for sparse hybrid retrieval if not already present
    op.execute("""
    DO $$ 
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'vendor_knowledge' AND column_name = 'tsv_content'
        ) THEN
            ALTER TABLE vendor_knowledge 
                ADD COLUMN tsv_content tsvector 
                GENERATED ALWAYS AS (
                    to_tsvector('english', coalesce(title, '') || ' ' || coalesce(vendor, '') || ' ' || coalesce(protocol, '') || ' ' || chunk_text)
                ) STORED;
        END IF;
    END $$;
    """)

    # 4. Indexes for vendor_knowledge (Dense HNSW + Sparse GIN + B-Tree)
    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_vendor_knowledge_embedding 
        ON vendor_knowledge USING hnsw (embedding vector_cosine_ops);
    """)

    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_vendor_knowledge_tsv 
        ON vendor_knowledge USING gin(tsv_content);
    """)

    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_vendor_knowledge_vendor_proto 
        ON vendor_knowledge(vendor, protocol);
    """)

    # 5. Baseline troubleshooting_audit_ledger table
    op.execute("""
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
    """)

    # 6. Indexes for troubleshooting_audit_ledger
    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_audit_ledger_device_vendor 
        ON troubleshooting_audit_ledger(device_id, vendor);
    """)

    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_audit_ledger_created_at 
        ON troubleshooting_audit_ledger(created_at DESC);
    """)


def downgrade() -> None:
    # Safe teardown of baseline objects
    op.execute("DROP TABLE IF EXISTS troubleshooting_audit_ledger CASCADE;")
    op.execute("DROP TABLE IF EXISTS vendor_knowledge CASCADE;")
    # Note: pgvector extension is kept intact to prevent impacting other databases/extensions
