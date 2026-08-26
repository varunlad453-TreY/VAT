# System Architecture: Vendor-Aware Troubleshooting (VAT Enterprise)

**Canonical Source of Truth for Architecture & Technical Specifications**

---

## 1. Architectural Philosophy & Design Principles

VAT Enterprise is built around three core architectural tenets:

1. **Deterministic Grounding (Zero Speculative Hallucination)**:
   Remediating core carrier infrastructure (e.g. Cisco ASR 9000, Juniper MX960, Arista 7280R) requires exact CLI syntax and strict adherence to official TAC manuals. The system enforces strict RAG grounding where every remediation step is tied to an indexed documentation chunk.

2. **Graceful Degradation (Air-Gapped & Offline Resilience)**:
   In mission-critical carrier environments where external database or cloud LLM connectivity may be unavailable, the platform automatically degrades to its high-precision in-memory multi-vendor corpus and deterministic playbook generator without service interruption.

3. **4-Stage Safe Remediation Lifecycle**:
   Network changes are never proposed as bare commands. Every playbook enforces sequential execution: `Pre-Check (Read-Only)` $\rightarrow$ `Remediation (Configuration Fix)` $\rightarrow$ `Post-Check (Convergence)` $\rightarrow$ `Rollback Playbook (Fail-Safe)`.

---

## 2. Layered Component Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                 LAYER 1: PRESENTATION & UI                               │
│  • High-Density NOC Operational Split-Pane Canvas (frontend/index.html, styles.css)      │
│  • Event Controller & Export Engine (frontend/app.js)                                    │
│  • Real-Time Incident Stream, Live UTC Clock, Telemetry Ingestion Editor                 │
└────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                             │ HTTP REST / JSON
┌────────────────────────────────────────────▼─────────────────────────────────────────────┐
│                                 LAYER 2: API & ROUTING                                   │
│  • FastAPI Application Server (backend/main.py:8000)                                     │
│  • Telemetry Router (/telemetry/parse, /telemetry/ingest) (backend/routes/telemetry.py)  │
│  • Troubleshoot Router (/troubleshoot, /sources, /audit) (backend/routes/troubleshoot.py) │
│  • Health & Metadata Endpoints (/health, /)                                              │
└────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                             │ Pydantic Validated Payloads
┌────────────────────────────────────────────▼─────────────────────────────────────────────┐
│                            LAYER 3: TELEMETRY PARSING & NORMALIZATION                    │
│  • TelemetryParserService (backend/services/telemetry_parser.py)                         │
│  • Multi-Vendor Regex Tokenizer (Cisco IOS-XE/XR, Junos, VMware VeloCloud, Arista EOS)   │
│  • Event Code, Protocol, Interface, Peer IP, Severity, and Category Extraction           │
└────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                             │ Normalized Telemetry (ParsedTelemetry)
┌────────────────────────────────────────────▼─────────────────────────────────────────────┐
│                         LAYER 4: HYBRID VECTOR SEARCH & RAG RETRIEVAL                    │
│  • VectorService (backend/services/vector_service.py)                                    │
│  • Dense Search: 384-dim all-MiniLM-L6-v2 embeddings + pgvector HNSW Cosine Distance     │
│  • Sparse Search: PostgreSQL tsvector Full-Text Search + ts_rank_cd BM25 scoring         │
│  • Fusion Algorithm: Reciprocal Rank Fusion (RRF: 65% Dense + 35% Sparse)                │
│  • Air-Gapped Fallback: Multi-Vendor In-Memory Indexed Corpus                            │
└────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                             │ Ranked Citations (VendorDocCitation[])
┌────────────────────────────────────────────▼─────────────────────────────────────────────┐
│                            LAYER 5: AI SYNTHESIS & RUNBOOK GENERATION                    │
│  • AIService (backend/services/ai_service.py)                                            │
│  • LLM Engine: OpenAI / Azure / GitHub Models API (via AsyncOpenAI JSON mode)            │
│  • Deterministic Engine: Multi-vendor anomaly synthesis with blast radius assessment     │
│  • 4-Stage Playbook: Pre-Checks, Remediation CLI, Post-Checks, Safe Rollbacks            │
└────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                             │ Async Persistence (asyncpg)
┌────────────────────────────────────────────▼─────────────────────────────────────────────┐
│                             LAYER 6: PERSISTENCE & AUDIT LEDGER                          │
│  • PostgreSQL 16 with pgvector extension (docker-compose.yml, schemas/postgres/)         │
│  • vendor_knowledge: Documentation chunks, embeddings, tsvector content, GIN/HNSW indexes │
│  • troubleshooting_audit_ledger: Permanent execution logs, JSONB steps, risk metadata   │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Database Schema & Indexing Architecture

The database architecture is defined in [02_hybrid_vector_schema.sql](file:///g:/VAT/schemas/postgres/02_hybrid_vector_schema.sql):

### 3.1 `vendor_knowledge` Table (Knowledge Base Store)
Stores chunked vendor manuals with dense vector embeddings and generated full-text search tokens.

```sql
CREATE TABLE vendor_knowledge (
    id SERIAL PRIMARY KEY,
    source_url TEXT NOT NULL,
    title TEXT,
    vendor VARCHAR(64) NOT NULL DEFAULT 'cisco',
    product_family VARCHAR(64) DEFAULT 'routing',
    protocol VARCHAR(32) DEFAULT 'ospf',
    error_codes TEXT[] DEFAULT '{}',
    chunk_text TEXT NOT NULL,
    embedding vector(384),
    tsv_content tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(title, '') || ' ' || coalesce(vendor, '') || ' ' || coalesce(protocol, '') || ' ' || chunk_text)
    ) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### Specialized Indexes:
- **`idx_vendor_knowledge_embedding`**: `USING hnsw (embedding vector_cosine_ops)` for sub-millisecond approximate nearest neighbor (ANN) cosine vector search.
- **`idx_vendor_knowledge_tsv`**: `USING gin(tsv_content)` for rapid inverted full-text keyword search.
- **`idx_vendor_knowledge_vendor_proto`**: B-Tree composite index on `(vendor, protocol)` for partition filtering.

---

### 3.2 `troubleshooting_audit_ledger` Table (Compliance & History)
Stores immutable records of all executed troubleshooting sessions for compliance, SLA tracking, and post-mortem analysis.

```sql
CREATE TABLE troubleshooting_audit_ledger (
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
```

---

## 4. Resilience & Fallback Mechanics

| Component | Primary Mode (Production Cloud/DB) | Fallback Mode (Air-Gapped / Disconnected) |
| :--- | :--- | :--- |
| **Database Pool** | Async `asyncpg.create_pool` with `register_vector` | Automatic connection deferral; operations continue in-memory |
| **Embeddings** | `SentenceTransformer("all-MiniLM-L6-v2")` | Deterministic SHA-256 normalized vector generator |
| **Vector Search** | PostgreSQL HNSW Cosine + BM25 tsvector GIN via RRF | Multi-Vendor in-memory scored fallback corpus (`ENTERPRISE_FALLBACK_CORPUS`) |
| **LLM Synthesis** | OpenAI / Azure Inference API via `AsyncOpenAI` | Deterministic 4-stage multi-vendor runbook generator |
| **Audit Logging** | Async INSERT into `troubleshooting_audit_ledger` | In-memory log capture with console output |

---

## 5. Security & Isolation Model

- **No Hardcoded Credentials**: Database passwords and API tokens are loaded exclusively via environment variables and `.env` files via Pydantic `BaseSettings`.
- **Read-Only Pre-Check Guarantee**: Phase 1 commands are strictly validated as non-destructive inspection queries (`show`, `ping`, `remote_diagnostics`).
- **Strict Parameter Normalization**: All incoming syslog strings and JSON payloads undergo Pydantic v2 schema validation and XSS escaping in the UI.
