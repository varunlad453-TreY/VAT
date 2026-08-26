# Vendor-Aware AI Troubleshooter (VAT Enterprise)

**Carrier-Grade Multi-Vendor Network Diagnostic & Automated Remediation Platform**

VAT is an enterprise network intelligence and incident remediation system designed for Tier-1 telecom carriers, internet service providers (ISPs), and large-scale enterprise backbones. It ingests raw multi-vendor network error telemetry (syslogs, trap events, and interface flaps), executes **hybrid vector search (pgvector HNSW + BM25 RRF)** against official vendor documentation, and automatically synthesizes a deterministic **4-stage remediation runbook** with blast radius risk scoring and automated rollback playbooks.

---

## Current Platform Capabilities

| Capability | Supported Platforms / Specs | Implementation Status |
| :--- | :--- | :--- |
| **Multi-Vendor Telemetry Parsing** | Cisco (IOS-XE/XR), Juniper (Junos), VMware VeloCloud SD-WAN, Arista (EOS) | **IMPLEMENTED** (Regex & token extraction) |
| **Dense Vector Similarity Search** | 384-dim embeddings (`all-MiniLM-L6-v2`), PostgreSQL `pgvector` HNSW Cosine Index | **IMPLEMENTED** (with in-memory fallback) |
| **Sparse Lexical Search** | PostgreSQL `tsvector` + GIN Index (`ts_rank_cd`) | **IMPLEMENTED** (with in-memory fallback) |
| **Hybrid Search Fusion** | Reciprocal Rank Fusion (RRF: 65% dense cosine + 35% sparse BM25) | **IMPLEMENTED** |
| **4-Stage Remediation Runbook** | Pre-Checks (Read-Only) $\rightarrow$ Remediation CLI $\rightarrow$ Post-Checks $\rightarrow$ Safe Rollback | **IMPLEMENTED** |
| **Operational Risk & Blast Radius** | Risk Classification (`LOW`, `MEDIUM`, `HIGH`), MTTR estimation, Impact scope | **IMPLEMENTED** |
| **Permanent Audit Ledger** | PostgreSQL `troubleshooting_audit_ledger` table with JSONB step preservation | **IMPLEMENTED** |
| **NOC Console UI** | High-density canvas split-pane interface (zero emojis, zero card grids) | **IMPLEMENTED** (`/console`) |
| **Runbook Export Utilities** | 1-Click Copy Full CLI script, Export JSON Runbook, Export Markdown Report | **IMPLEMENTED** |
| **LLM Synthesis (Cloud)** | OpenAI / GitHub Models / Azure Inference API integration | **IMPLEMENTED** (Optional via API Key) |
| **Deterministic Offline Synthesis** | Air-gapped fallback RAG synthesizer matching indexed vendor TAC manuals | **IMPLEMENTED** (Active when offline) |

---

## System Architecture Overview

```
                          [ RAW CARRIER TELEMETRY / SYSLOG ]
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │    FastAPI Application Server        │
                      │       (backend/main.py:8000)         │
                      └──────────────────┬───────────────────┘
                                         │
                ┌────────────────────────┴────────────────────────┐
                ▼                                                 ▼
   ┌──────────────────────────┐                      ┌──────────────────────────┐
   │  TelemetryParserService  │                      │    NOC Console (UI)      │
   │  (Regex & Token Normal)  │                      │   (frontend/index.html)  │
   └────────────┬─────────────┘                      └──────────────────────────┘
                │
                ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │                    AIService & VectorService (RAG)                     │
   ├────────────────────────────────────┬───────────────────────────────────┤
   │ Dense Search (pgvector HNSW)       │ Sparse Lexical (tsvector GIN BM25)│
   │ 384-dim SentenceTransformer        │ Reciprocal Rank Fusion (RRF)      │
   └────────────────────────────────────┴───────────────────────────────────┘
                                         │
                         ┌───────────────┴───────────────┐
                         ▼                               ▼
            ┌──────────────────────────┐   ┌───────────────────────────┐
            │   PostgreSQL 16 DB       │   │  In-Memory Fallback Corpus│
            │   (pgvector + Ledger)    │   │  (Air-gapped Multi-Vendor)│
            └──────────────────────────┘   └───────────────────────────┘
                                         │
                                         ▼
            ┌──────────────────────────────────────────────────────────┐
            │         4-STAGE SYNTHESIZED REMEDIATION PLAYBOOK         │
            │  1. Pre-Checks (Read-Only Inspection)                    │
            │  2. Target Configuration Remediation (CLI Fix)           │
            │  3. Post-Checks (Route Convergence Validation)           │
            │  4. Zero-Downtime Safe Rollback (Emergency Plan)         │
            └──────────────────────────────────────────────────────────┘
```

---

## Tech Stack

- **Backend**: Python 3.10+ / 3.14, FastAPI, Uvicorn, Pydantic v2, Pydantic Settings
- **Database & Search**: PostgreSQL 16 (`pgvector/pgvector:pg16`), asyncpg, HNSW Cosine Index, GIN `tsvector`
- **Embeddings & NLP**: `sentence-transformers` (`all-MiniLM-L6-v2`), PyTorch, OpenAI API client
- **Frontend**: Vanilla HTML5, CSS3 Custom Properties Design System (Obsidian Slate), ES6+ JavaScript
- **Testing & QA**: Pytest, Pytest-Asyncio, HTTPX, TestClient

---

## Repository Structure

```
g:/VAT/
├── .env                              # Environment configuration (DB, API keys, models)
├── docker-compose.yml                # PostgreSQL 16 + pgvector container definition
├── requirements.txt                  # Python dependencies
├── backend/
│   ├── main.py                       # FastAPI application entrypoint & static routes
│   ├── database/
│   │   └── client.py                 # Async asyncpg pool manager with pgvector codecs
│   ├── models/
│   │   ├── remediation.py            # Pydantic models for 4-stage runbooks & audit ledger
│   │   └── troubleshoot.py           # Pydantic models for requests, responses & citations
│   ├── routes/
│   │   ├── telemetry.py              # Telemetry parsing & batch ingestion routes
│   │   └── troubleshoot.py           # Diagnostic synthesis, sources & audit history routes
│   └── services/
│       ├── ai_service.py             # LLM & deterministic RAG playbook synthesis engine
│       ├── telemetry_parser.py       # Multi-vendor regex tokenization & extraction service
│       └── vector_service.py         # Hybrid HNSW + BM25 RRF vector search service
├── config/
│   └── settings.py                   # Centralized Pydantic BaseSettings singleton
├── docs/                             # Canonical architecture, API & data flow documentation
│   ├── ARCHITECTURE.md               # Detailed system and database architecture
│   ├── API_REFERENCE.md              # REST API endpoint contracts and payloads
│   ├── DATA_FLOW.md                  # Step-by-step telemetry ingestion & RAG lifecycle
│   ├── HYBRID_RAG_AND_VECTOR_SEARCH.md # Dense + sparse retrieval & embedding details
│   ├── REMEDIATION_RUNBOOK_LIFECYCLE.md# 4-stage operational model & safety rules
│   ├── SETUP_AND_DEPLOYMENT.md       # Local setup, Docker, and production deployment
│   ├── TELEMETRY_AND_PARSING.md      # Multi-vendor syslog normalization rules
│   ├── TESTING_AND_QA.md             # Test suite execution, coverage & validation
│   └── ROADMAP_AND_STATUS.md         # Truthful feature status, limitations & roadmap
├── frontend/
│   ├── app.js                        # NOC console UI state controller & export actions
│   ├── index.html                    # High-density operational split-pane canvas
│   └── styles.css                    # Obsidian dark mode design system (zero card-grid)
├── schemas/postgres/
│   ├── 01_vector_schema.sql          # Base pgvector table & HNSW index definition
│   └── 02_hybrid_vector_schema.sql   # Phase 2 hybrid tsvector, GIN index & audit ledger
├── scripts/
│   └── ingest_vendor_docs.py         # Multi-vendor documentation ETL & indexing pipeline
└── tests/
    ├── test_enterprise_multivendor.py# Multi-vendor parser, hybrid search & API tests
    └── test_vendor_rag_troubleshooter.py # Embedding, chunking, RAG & endpoint unit tests
```

---

## Quickstart & Local Setup

### 1. Clone & Install Dependencies
```powershell
git clone <repo-url>
cd g:\VAT
python -m pip install -r requirements.txt
```

### 2. (Optional) Start PostgreSQL pgvector with Docker
```powershell
docker-compose up -d
```
*Note: If PostgreSQL is not running, the application automatically operates using its built-in multi-vendor in-memory fallback corpus with 100% functionality.*

### 3. (Optional) Seed Vendor Documentation
```powershell
python scripts/ingest_vendor_docs.py
```

### 4. Start the Application Server
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 5. Access Endpoints
- **NOC Operational Console**: [http://127.0.0.1:8000/console](http://127.0.0.1:8000/console)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check Probe**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## Running Automated Tests

Run the full Pytest test suite:
```powershell
pytest tests/ -v
```
All **25 tests** validate:
- Multi-vendor syslog parsing (Cisco, Juniper, VeloCloud, Arista)
- Vector embedding generation and chunk overlap calculation
- Hybrid search ranking and fallback corpus retrieval
- End-to-end 4-stage playbook synthesis and blast radius risk classification
- REST API endpoint contracts (`/troubleshoot`, `/telemetry/ingest`, `/telemetry/parse`, `/health`, `/console`)

---

## Canonical Documentation Index

For complete and authoritative technical specifications, refer to the documentation directory:

1. [Architecture & System Design](file:///g:/VAT/docs/ARCHITECTURE.md)
2. [Data Flow & Sequence Diagrams](file:///g:/VAT/docs/DATA_FLOW.md)
3. [REST API Reference & Schemas](file:///g:/VAT/docs/API_REFERENCE.md)
4. [Hybrid RAG & Vector Search Engine](file:///g:/VAT/docs/HYBRID_RAG_AND_VECTOR_SEARCH.md)
5. [Telemetry Parsing & Multi-Vendor Normalization](file:///g:/VAT/docs/TELEMETRY_AND_PARSING.md)
6. [Remediation Runbook Lifecycle & Safety](file:///g:/VAT/docs/REMEDIATION_RUNBOOK_LIFECYCLE.md)
7. [Setup, Configuration & Deployment Guide](file:///g:/VAT/docs/SETUP_AND_DEPLOYMENT.md)
8. [Testing & Quality Assurance](file:///g:/VAT/docs/TESTING_AND_QA.md)
9. [Feature Status, Technical Debt & Roadmap](file:///g:/VAT/docs/ROADMAP_AND_STATUS.md)
