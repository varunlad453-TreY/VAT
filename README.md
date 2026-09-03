# Vendor-Aware AI Troubleshooter (VAT Enterprise)

**Carrier-Grade Multi-Vendor Network Diagnostic & Automated Remediation Platform**

[![CI Pipeline](https://github.com/varunlad453-TreY/VAT/actions/workflows/ci.yaml/badge.svg)](https://github.com/varunlad453-TreY/VAT/actions/workflows/ci.yaml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14.2+-black.svg)](https://nextjs.org/)
[![Tests](https://img.shields.io/badge/tests-75%2F75%20passing-brightgreen.svg)](tests/)

VAT Enterprise is an automated network intelligence and incident remediation platform built for Tier-1 telecom carriers, internet service providers (ISPs), and large enterprise backbones. Operating on a distributed **CQRS (Command Query Responsibility Segregation)** event-driven architecture, VAT ingests multi-vendor network telemetry (syslog, flaps, traps), executes **hybrid dense-sparse vector search (Qdrant / pgvector HNSW + BM25 RRF)** against official vendor documentation, and synthesizes deterministic **4-stage remediation runbooks** (Pre-Checks $\rightarrow$ Target CLI Fix $\rightarrow$ Post-Checks $\rightarrow$ Safe Rollback) with blast radius risk scoring.

---

## 1. Current Platform Capabilities

| Capability Area | Implemented Specification | Codebase Status | Real Implementation Notes |
| :--- | :--- | :--- | :--- |
| **Multi-Vendor Telemetry Parsing** | Cisco (IOS-XE/XR), Juniper (Junos), VMware VeloCloud SD-WAN, Arista (EOS) | **IMPLEMENTED** | Regex tokenization extracting vendor, event code, protocol, interface, peer IP, and severity in `backend/infrastructure/adapters/telemetry_parser_adapter.py`. |
| **Event Streaming Ingestion** | Vector Syslog Aggregator (UDP/TCP 514) $\rightarrow$ Redpanda Kafka broker (`vat.telemetry.*`) | **IMPLEMENTED** | Declarative pipelines in `config/vector/` and Redpanda streaming producer in `backend/infrastructure/streaming/`. |
| **High-Throughput Analytics** | ClickHouse 24.3 Kafka Engine (`vat.telemetry_raw`, `vat.telemetry_parsed`) | **IMPLEMENTED** | Schema in `config/clickhouse/` and analytics repository in `backend/infrastructure/repositories/`. |
| **Decoupled Embedding Microservice** | FastAPI microservice on port 8001 serving 384-dim embeddings (`all-MiniLM-L6-v2`) | **IMPLEMENTED** | Located in `services/embedding_service/` with Prometheus metrics and PyTorch acceleration. |
| **Hybrid Dense + Sparse Search** | Dense Cosine (pgvector HNSW / Qdrant) + Sparse Lexical (PostgreSQL tsvector GIN) | **IMPLEMENTED** | Reciprocal Rank Fusion (RRF: 65% dense + 35% sparse) in `backend/infrastructure/repositories/`. |
| **Air-Gapped Resilient Fallback** | In-Memory Scored Corpus (`ENTERPRISE_FALLBACK_CORPUS`) with normalized vectors | **IMPLEMENTED** | 100% operational when external databases or embedding workers are offline (`in_memory_repository.py`). |
| **4-Stage Remediation Runbook** | Pre-Checks (Read-Only) $\rightarrow$ Target CLI Fix $\rightarrow$ Post-Checks $\rightarrow$ Safe Rollback | **IMPLEMENTED** | Enforced by domain models in `backend/domain/entities/remediation.py`. |
| **Operational Risk & Blast Radius** | Risk Classification (`LOW`, `MEDIUM`, `HIGH`), MTTR estimation, and impact scope | **IMPLEMENTED** | Assessed deterministically from syslog severity and protocol impact scope. |
| **Deterministic Synthesis Engine** | Offline rule-based TAC synthesizer matching vendor manual fault signatures | **IMPLEMENTED** | Active when cloud LLM API key is absent (`backend/infrastructure/adapters/deterministic_synthesizer.py`). |
| **LLM Cloud Synthesis (Optional)** | OpenAI / Azure / GitHub Models API via `AsyncOpenAI` JSON mode | **IMPLEMENTED** | Optional enhancement via `OPENAI_API_KEY` (`backend/infrastructure/adapters/resilient_llm_adapter.py`). |
| **Permanent Audit Ledger** | PostgreSQL `troubleshooting_audit_ledger` with immutable JSONB execution history | **IMPLEMENTED** | Managed by `backend/infrastructure/repositories/audit_repository.py`. |
| **Modern NOC Web Application** | Next.js 14, React Query, Zustand, Tailwind CSS, WebSockets streaming | **IMPLEMENTED** | Production frontend located under `frontend/src/`. |
| **Legacy Split-Pane Console** | High-density canvas interface with preset incidents and CLI copy | **IMPLEMENTED** | Served directly by FastAPI at `/console` via `frontend/index.html`. |
| **Real-Time WebSockets** | Live telemetry streaming (`/ws/telemetry`) & runbook synthesis progress (`/ws/troubleshoot`) | **IMPLEMENTED** | WebSockets controllers in `backend/presentation/websockets/`. |
| **SRE Alerting & Observability** | Multi-window multi-burn-rate error budget alerts + OpenTelemetry tail sampling | **IMPLEMENTED** | Configured in `k8s/` and documented in `docs/platform-runbook.md`. |
| **Day-4 Cloud-Native Operations** | Istio mTLS, Vault/ESO secrets, Postgres RLS, KEDA GPU scale-to-zero, Karpenter Spot | **STAGED (GitOps)** | 24 declarative manifests staged under `k8s/` with full empirical verification. |
| **Network Topology Graph Engine** | Graph-based network topology mapping & link state visualization | **NOT IMPLEMENTED** | Out of architectural scope; VAT is an incident diagnostic & remediation engine. |
| **Network Path Trace / Latency Probe** | Hop-by-hop path tracing, synthetic ping, or latency hop calculation | **NOT IMPLEMENTED** | Out of architectural scope. |
| **Active SNMP / gNMI Polling** | Active polling of physical routers for interface counters or state tables | **NOT IMPLEMENTED** | The platform is a passive receiver of telemetry streams and syslog events. |
| **Automated Direct-Device Execution** | Pushing commands directly to routers via Netconf/SSH without human intervention | **NOT IMPLEMENTED** | Safety architecture enforces human-in-the-loop review (1-click copy / JSON / Markdown export). |

---

## 2. System Architecture Overview

```
                                  [ RAW CARRIER TELEMETRY / SYSLOG ]
                                                 │
                                                 ▼
                       ┌──────────────────────────────────────────────────┐
                       │           Vector Telemetry Aggregator            │
                       │           (UDP/TCP Port 514 Syslog Sink)         │
                       └─────────────────────────┬────────────────────────┘
                                                 │
                                                 ▼
                       ┌──────────────────────────────────────────────────┐
                       │          Redpanda Distributed Broker             │
                       │       Topics: vat.telemetry.raw / .parsed        │
                       └─────────────────────────┬────────────────────────┘
                                                 │
                        ┌────────────────────────┴────────────────────────┐
                        ▼                                                 ▼
       ┌─────────────────────────────────┐               ┌─────────────────────────────────┐
       │     ClickHouse 24.3 Cluster     │               │   FastAPI Application Server    │
       │   (Real-Time Analytics Tier)    │               │     (Clean / Hexagonal Core)    │
       └─────────────────────────────────┘               └────────────────┬────────────────┘
                                                                          │
                        ┌─────────────────────────────────────────────────┴─────────────────────────────────┐
                        ▼                                                                                   ▼
       ┌─────────────────────────────────┐                                                 ┌─────────────────────────────────┐
       │     Decoupled Embedding Service │                                                 │     Persistence & State Tier    │
       │    (services/embedding_service) │                                                 │ • PostgreSQL 16 (pgvector/RLS)  │
       │  FastAPI + PyTorch (Port 8001)  │                                                 │ • Qdrant (Distributed Vectors)  │
       └────────────────┬────────────────┘                                                 │ • Redis (Cache & Pub/Sub)       │
                        │ 384-dim Embeddings                                               └────────────────┬────────────────┘
                        ▼                                                                                   │
       ┌──────────────────────────────────────────────────────────────────────────────────┐                 │
       │                        Hybrid Vector Search & RAG Fusion                         │                 │
       │  • Dense ANN Search: pgvector HNSW / Qdrant                                      │                 │
       │  • Sparse Search: PostgreSQL tsvector GIN (ts_rank_cd BM25)                      │                 │
       │  • Fusion Algorithm: Reciprocal Rank Fusion (65% Dense + 35% Sparse)             │                 │
       │  • Air-Gapped Resilient Fallback: ENTERPRISE_FALLBACK_CORPUS                     │                 │
       └────────────────────────────────────────┬─────────────────────────────────────────┘                 │
                                                │ Ranked TAC Manual Chunks                                  │
                                                ▼                                                           │
       ┌──────────────────────────────────────────────────────────────────────────────────┐                 │
       │                     AIService & Deterministic Synthesizer                        │                 │
       │  • Deterministic Rule Engine (Zero hallucination, air-gapped TAC manuals)        │                 │
       │  • Resilient LLM Adapter (OpenAI / Azure JSON mode when API key provided)        │                 │
       │  • 4-Stage Playbook Synthesis + Blast Radius Risk Classifier                     │                 │
       └────────────────────────────────────────┬─────────────────────────────────────────┘                 │
                                                │ Structured 4-Stage Playbook                               │
                                                ▼                                                           │
                       ┌──────────────────────────────────────────────────┐                                 │
                       │             Presentation & NOC Consoles          │◄────────────────────────────────┘
                       ├──────────────────────────────────────────────────┤
                       │ 1. Modern Web Application: Next.js 14, React 18, │
                       │    Zustand, React Query, WebSockets (/ws/*)      │
                       │ 2. Operational NOC Canvas: High-density vanilla  │
                       │    split-pane interface served at /console       │
                       └──────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

- **Backend Application**: Python 3.10+, FastAPI 0.110+, Uvicorn, Pydantic v2, Pydantic Settings, `asyncpg`, `httpx`, `aiokafka`, `redis-py`.
- **Decoupled Embedding Microservice**: FastAPI, PyTorch, `sentence-transformers` (`all-MiniLM-L6-v2`), Prometheus Client.
- **Data Persistence & Analytics**:
  - PostgreSQL 16 with `pgvector` extension (transactional state, audit ledger, HNSW vector indexes).
  - ClickHouse 24.3 (high-throughput raw and parsed telemetry analytics).
  - Qdrant (distributed vector storage).
  - Redis (caching and pub/sub).
- **Streaming & Ingestion**: Redpanda (Kafka-compatible event broker), Vector (Syslog ingestion daemon).
- **Frontend Applications**:
  - Modern Application: Next.js 14 (App Router), TypeScript, React Query, Zustand, Tailwind CSS.
  - Legacy NOC Console: Vanilla HTML5, CSS3 Custom Properties (Obsidian Slate design system), ES6+ JavaScript.
- **Testing & Quality Assurance**: Pytest, Pytest-Asyncio, HTTPX TestClient (75 automated tests).
- **Cloud-Native Infrastructure & Day-4 Ops**: Kubernetes, Helm, Istio 1.22+, HashiCorp Vault, External Secrets Operator, KEDA 2.14+, Karpenter v0.35+, Loft vcluster, Tilt, Chaos Mesh.

---

## 4. Repository Structure

```
g:/VAT/
├── .env                              # Local environment configuration
├── .env.example                      # Template of all required and optional environment variables
├── docker-compose.yml                # Multi-service local stack (PostgreSQL, Redpanda, ClickHouse, Qdrant, Redis)
├── requirements.txt                  # Root Python dependencies
├── Tiltfile                          # Starlark live code sync script (<2s hot reload)
├── alembic/                          # Database schema migration versions
│   └── versions/
│       └── 0001_initial_baseline.py  # Baseline schema definitions
├── backend/                          # Clean / Hexagonal Backend Architecture
│   ├── main.py                       # FastAPI application entrypoint & router registration
│   ├── application/                  # Use cases, DTOs, and interface ports
│   │   ├── dtos/                     # Data Transfer Objects
│   │   ├── ports/                    # Repository and service interfaces
│   │   └── use_cases/                # Business logic orchestration
│   ├── domain/                       # Domain entities, enums, and exceptions
│   │   ├── entities/                 # RawTelemetry, ParsedTelemetry, RemediationPlaybook
│   │   ├── enums.py                  # VendorType, SeverityLevel, RiskLevel, ProtocolType
│   │   └── exceptions.py             # Domain-level exceptions
│   ├── infrastructure/               # Concrete adapters, repositories, and clients
│   │   ├── adapters/                 # Parsers, LLM adapters, deterministic synthesizers
│   │   ├── ai/                       # Remote embedding client
│   │   ├── cache/                    # Redis cache service
│   │   ├── repositories/             # PostgreSQL, Qdrant, ClickHouse, In-Memory repositories
│   │   └── streaming/                # Redpanda Kafka streaming producer
│   └── presentation/                 # Presentation controllers
│       ├── api/                      # REST routers (/troubleshoot, /telemetry, /health)
│       └── websockets/               # WebSockets routers (/ws/telemetry, /ws/troubleshoot)
├── config/                           # Infrastructure configurations
│   ├── clickhouse/                   # ClickHouse DDL and Kafka Engine tables
│   ├── settings.py                   # Pydantic BaseSettings singleton
│   └── vector/                       # Vector daemon pipeline configurations
├── docs/                             # Canonical System Documentation
│   ├── ARCHITECTURE.md               # Detailed system design, CQRS data plane & domain architecture
│   ├── API_REFERENCE.md              # REST & WebSockets endpoint contracts, schemas, and codes
│   ├── DATA_FLOW.md                  # Telemetry ingestion, streaming & RAG sequence flows
│   ├── HYBRID_RAG_AND_VECTOR_SEARCH.md # Dense + sparse retrieval & embedding worker architecture
│   ├── REMEDIATION_RUNBOOK_LIFECYCLE.md# 4-stage operational model & safety guidelines
│   ├── ROADMAP_AND_STATUS.md         # Truthful feature implementation matrix & technical debt
│   ├── SETUP_AND_DEPLOYMENT.md       # Development setup, Docker Compose, Tilt, and K8s rollout
│   ├── TELEMETRY_AND_PARSING.md      # Multi-vendor syslog normalization rules
│   ├── TESTING_AND_QA.md             # Test inventory (75 tests), test architecture & CI/CD
│   ├── platform-runbook.md           # Carrier-grade SRE incident response runbooks
│   └── Handoff/                      # Chronological development logs (1_Handoff.md - 7_Handoff.md)
├── frontend/                         # User Interface Tier
│   ├── src/                          # Modern Next.js 14 App (React, Query, Zustand, Tailwind)
│   ├── index.html                    # Legacy NOC Operational Split-Pane Canvas (served at /console)
│   ├── app.js                        # Legacy console DOM controller
│   └── styles.css                    # Obsidian Slate styling
├── k8s/                              # Declarative Kubernetes Manifests (Day-2, Day-3, Day-4)
│   ├── chaos/                        # Chaos Mesh schedules & network partition tests
│   ├── devex/                        # Loft vcluster virtual dev sandboxes
│   ├── disaster-recovery/            # Redpanda MirrorMaker 2, Postgres CNPG, Route53 failover
│   ├── finops/                       # KEDA GPU scale-to-zero, Karpenter Spot NodePools
│   ├── gitops/                       # ArgoCD ApplicationSets and root application
│   └── security/                     # Istio STRICT mTLS, Vault/ESO secrets, Postgres RLS, ClickHouse RBAC
├── services/
│   └── embedding_service/            # Decoupled GPU/CPU embedding microservice (Port 8001)
└── tests/                            # Comprehensive Automated Test Suite (75 Tests)
```

---

## 5. Quickstart & Local Development

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Node.js 18+ and `npm`
- (Optional) Docker & Docker Compose for multi-service persistence

### Step 1: Clone Repository & Configure Environment
```bash
git clone https://github.com/varunlad453-TreY/VAT.git
cd VAT
cp .env.example .env
```

### Step 2: Install Python Dependencies
```bash
python -m pip install -r requirements.txt
```

### Step 3: Start Supporting Services (Docker Compose)
To start PostgreSQL (pgvector), Redpanda, ClickHouse, and Redis:
```bash
docker-compose up -d
```
*Note: If Docker is not running, the application automatically activates its built-in in-memory fallback corpus and deterministic synthesizer with zero crashes.*

### Step 4: Start the Decoupled Embedding Worker (Port 8001)
```bash
python -m uvicorn services.embedding_service.main:app --host 0.0.0.0 --port 8001
```

### Step 5: Start the Backend Application Server (Port 8000)
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 6: Start the Modern Next.js Frontend (Port 3000)
```bash
cd frontend
npm install
npm run dev
```

### Step 7: Access Endpoints
- **Modern NOC Web Application**: [http://localhost:3000](http://localhost:3000)
- **High-Density Legacy Console**: [http://localhost:8000/console](http://localhost:8000/console)
- **Interactive Swagger REST Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Probe**: [http://localhost:8000/health](http://localhost:8000/health)
- **Embedding Worker Health & Metrics**: [http://localhost:8001/health](http://localhost:8001/health) | [http://localhost:8001/metrics](http://localhost:8001/metrics)

---

## 6. Running Automated Tests

Run the full automated test suite using Pytest:
```bash
pytest tests/ -v
```

All **75 tests** validate:
- Multi-vendor syslog parsing (Cisco, Juniper, VeloCloud, Arista).
- In-memory, pgvector, and Qdrant hybrid vector search ranking.
- 4-stage playbook generation, risk classification, and rollback mechanics.
- Decoupled embedding microservice HTTP contract, fallback handling, and metrics.
- Presentation REST controllers and real-time WebSockets streaming.
- Polyglot persistence, ClickHouse Kafka schemas, and Redpanda consumer loops.
- Chaos Mesh experiments and ArgoCD GitOps pipelines.

---

## 7. Canonical Documentation System

| Canonical Document | Scope & Contents |
| :--- | :--- |
| **[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)** | Full CQRS event-driven architecture, Clean/Hexagonal layers, persistence engines, and Day-4 infrastructure. |
| **[`docs/DATA_FLOW.md`](docs/DATA_FLOW.md)** | Detailed synchronous RAG diagnosis flow and asynchronous streaming telemetry pipeline. |
| **[`docs/API_REFERENCE.md`](docs/API_REFERENCE.md)** | REST and WebSockets API specifications, schemas, error codes, and embedding microservice contracts. |
| **[`docs/ROADMAP_AND_STATUS.md`](docs/ROADMAP_AND_STATUS.md)** | Truthful feature matrix, scope boundaries (Topology & Path Trace marked NOT IMPLEMENTED), and technical debt. |
| **[`docs/SETUP_AND_DEPLOYMENT.md`](docs/SETUP_AND_DEPLOYMENT.md)** | Detailed developer onboarding, environment variables, Tilt development, and production Kubernetes deployment. |
| **[`docs/TESTING_AND_QA.md`](docs/TESTING_AND_QA.md)** | 75-test inventory, coverage breakdown, integration test harnesses, and CI/CD validation. |
| **[`docs/HYBRID_RAG_AND_VECTOR_SEARCH.md`](docs/HYBRID_RAG_AND_VECTOR_SEARCH.md)** | Mathematical specification of dense cosine + sparse BM25 RRF fusion and decoupled embedding worker. |
| **[`docs/TELEMETRY_AND_PARSING.md`](docs/TELEMETRY_AND_PARSING.md)** | Multi-vendor syslog tokenization rules, regex specifications, and Vector daemon integration. |
| **[`docs/REMEDIATION_RUNBOOK_LIFECYCLE.md`](docs/REMEDIATION_RUNBOOK_LIFECYCLE.md)** | 4-stage operational safety model, blast radius classification, and rollback playbooks. |
| **[`docs/platform-runbook.md`](docs/platform-runbook.md)** | Tier-1 SRE operational runbooks for database split-brain, ingestion lag, and GPU starvation. |
| **[`docs/Handoff/`](docs/Handoff/)** | Historical chronological session development logs (`1_Handoff.md` through `7_Handoff.md`). |
