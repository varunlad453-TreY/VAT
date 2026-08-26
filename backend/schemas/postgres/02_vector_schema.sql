-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Vendor Knowledge Base table for chunked vendor documentation and embeddings
CREATE TABLE IF NOT EXISTS vendor_knowledge (
    id SERIAL PRIMARY KEY,
    source_url TEXT NOT NULL,
    title TEXT,
    vendor VARCHAR(64) NOT NULL DEFAULT 'cisco',
    chunk_text TEXT NOT NULL,
    embedding vector(384),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- HNSW Cosine Index for ultra-fast vector similarity search
CREATE INDEX IF NOT EXISTS idx_vendor_knowledge_embedding 
    ON vendor_knowledge USING hnsw (embedding vector_cosine_ops);
