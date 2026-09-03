# System Architecture: Vendor-Aware Troubleshooting (VAT Enterprise)

**Canonical Source of Truth for Architecture, System Design & Technical Specifications**

---

## 1. Architectural Philosophy & Design Principles

VAT Enterprise is built around five foundational architectural tenets:

1. **Deterministic Grounding (Zero Speculative Hallucination)**:
   Remediating core carrier routing infrastructure (e.g. Cisco ASR 9000, Juniper MX960, Arista 7280R, VMware Edge) requires exact CLI syntax and strict compliance with official TAC manuals. The system enforces strict RAG grounding where every remediation step is derived from verified vendor documentation chunks.

2. **Graceful Degradation & Air-Gapped Resilience**:
   In mission-critical carrier NOC environments where database clusters, Kafka brokers, or cloud LLM APIs may experience downtime or complete network isolation, the platform automatically falls back to an embedded in-memory multi-vendor corpus (`ENTERPRISE_FALLBACK_CORPUS`) and deterministic rule-based playbook synthesis with zero service interruption.

3. **4-Stage Operational Safety Model**:
   Network changes are never proposed as bare, unvalidated commands. Every synthesized runbook enforces sequential operational discipline: `Pre-Checks (Read-Only Inspection)` $\rightarrow$ `Target CLI Remediation` $\rightarrow$ `Post-Checks (Convergence Validation)` $\rightarrow$ `Safe Rollback Playbook (Fail-Safe Emergency Plan)`.

4. **Command Query Responsibility Segregation (CQRS)**:
   High-velocity telemetry writes (100,000+ EPS) are decoupled from interactive NOC diagnostic queries. Ingestion is handled asynchronously by Vector and Redpanda, analytical telemetry is stored in ClickHouse, and vector/transactional state is partitioned between Qdrant and PostgreSQL 16.

5. **Clean / Hexagonal Architecture**:
   The core domain logic (`backend/domain/`) is completely decoupled from frameworks, transport layers, and databases. Use cases orchestrate business workflows via ports (`backend/application/ports/`), while external integrations (FastAPI, WebSockets, ClickHouse, PostgreSQL, Qdrant, Redpanda, OpenAI) are implemented as swappable infrastructure adapters.

---

## 2. Global Architecture Diagram

```
                                      CARRIER NETWORK TELEMETRY
                     [ Syslog UDP/TCP 514 / SNMP Traps / Interface Flaps / API Payloads ]
                                                  │
                                                  ▼
                         ┌──────────────────────────────────────────────────┐
                         │           Vector Ingestion DaemonSet             │
                         │             (k8s/vector/daemonset.yaml)          │
                         └────────────────────────┬─────────────────────────┘
                                                  │
                                                  ▼
                         ┌──────────────────────────────────────────────────┐
                         │            Redpanda Streaming Broker             │
                         │       Topics: vat.telemetry.raw / .parsed        │
                         │           (k8s/redpanda/statefulset.yaml)        │
                         └──────────────┬───────────────────┬───────────────┘
                                        │                   │
                                        ▼                   ▼
    ┌─────────────────────────────────────────┐       ┌─────────────────────────────────────────┐
    │         ClickHouse 24.3 Cluster         │       │        FastAPI Application Server       │
    │        (Real-Time Analytics Store)      │       │        (Clean / Hexagonal Backend)      │
    │  • Kafka Engine Ingestion               │       │  • Port 8000 (REST & WebSockets)        │
    │  • Columns: device_id, raw, parsed, ts  │       │  • Hexagonal Domain & Use Cases         │
    │  • Config: config/clickhouse/           │       │  • Entrypoint: backend/main.py          │
    └─────────────────────────────────────────┘       └────────────────────┬────────────────────┘
                                                                           │
                               ┌───────────────────────────────────────────┴───────────────────────────────────────────┐
                               ▼                                                                                       ▼
    ┌──────────────────────────────────────────────────┐                                    ┌──────────────────────────────────────────────────┐
    │           Decoupled Embedding Service            │                                    │             Polyglot Persistence Tier            │
    │          (services/embedding_service)            │                                    │  • PostgreSQL 16 (pgvector, RLS, Audit Ledger)   │
    │  • Port 8001 / Fast GPU/CPU Inference            │                                    │  • Qdrant Vector Database (Cosine Search)        │
    │  • all-MiniLM-L6-v2 (384-dimensional)            │                                    │  • Redis (Query Cache & Pub/Sub)                 │
    │  • Prometheus Metrics: /metrics                  │                                    │  • Air-Gapped Fallback: in_memory_repository.py  │
    └──────────────────────────┬───────────────────────┘                                    └──────────────────────────┬───────────────────────┘
                               │ 384-dim Dense Embeddings                                                              │
                               └───────────────────────────────────┬───────────────────────────────────────────────────┘
                                                                   │
                                                                   ▼
                                    ┌──────────────────────────────────────────────────────────────┐
                                    │              Hybrid Vector Search & RRF Engine               │
                                    │  • Dense Search: Qdrant / PostgreSQL pgvector HNSW           │
                                    │  • Sparse Search: PostgreSQL tsvector GIN (ts_rank_cd)       │
                                    │  • Fusion: Reciprocal Rank Fusion (65% Dense + 35% Sparse)   │
                                    │  • Fallback: ENTERPRISE_FALLBACK_CORPUS (Air-gapped)         │
                                    └──────────────────────────────┬───────────────────────────────┘
                                                                   │ Ranked TAC Manual Chunks
                                                                   ▼
                                    ┌──────────────────────────────────────────────────────────────┐
                                    │                    AIService Synthesizer                     │
                                    │  • Deterministic Synthesizer: Rule-based TAC manuals         │
                                    │  • Resilient LLM Adapter: OpenAI / Azure JSON mode           │
                                    │  • 4-Stage Playbook Engine + Blast Radius Classifier         │
                                    └──────────────────────────────┬───────────────────────────────┘
                                                                   │ Synthesized Playbook Payload
                                                                   ▼
                               ┌───────────────────────────────────────────────────────────────────┐
                               │                    Presentation & NOC Consoles                    │
                               ├─────────────────────────────────┬─────────────────────────────────┤
                               │ Modern Web Application:         │ Operational NOC Canvas:         │
                               │ • Next.js 14, React 18          │ • High-density split-pane UI    │
                               │ • TanStack React Query, Zustand │ • Vanilla HTML5/JS/CSS          │
                               │ • Real-Time WebSockets (/ws/*)  │ • Served at /console            │
                               │ • Path: frontend/src/           │ • Path: frontend/index.html     │
                               └─────────────────────────────────┴─────────────────────────────────┘
```

---

## 3. Backend Architecture: Clean / Hexagonal Design

The backend implementation (`backend/`) strictly adheres to clean architectural separation:

```
backend/
├── domain/                    # Enterprise Business Rules & Entities (Pure Python, Zero Frameworks)
│   ├── entities/              # RawTelemetry, ParsedTelemetry, RemediationPlaybook, RemediationStep
│   ├── enums.py               # VendorType, SeverityLevel, ProtocolType, RiskLevel, CategoryType
│   └── exceptions.py          # Domain exceptions (ParsingException, VectorSearchException, etc.)
│
├── application/               # Application Business Rules (Use Cases & Interfaces)
│   ├── dtos/                  # TelemetryDTO, TroubleshootRequestDTO, TroubleshootResponseDTO
│   ├── ports/                 # Input/Output port protocols (IVectorRepository, IAISynthesizer, etc.)
│   └── use_cases/             # IngestTelemetryBatchUseCase, SynthesizeRemediationRunbookUseCase
│
├── infrastructure/            # Frameworks, Drivers & Concrete Implementations
│   ├── adapters/              # TelemetryParserAdapter, ResilientLLMAdapter, DeterministicSynthesizer
│   ├── ai/                    # RemoteEmbeddingClient (HTTP to embedding worker on port 8001)
│   ├── cache/                 # RedisService (caching, TTL, pub/sub)
│   ├── repositories/          # PgVectorRepository, QdrantVectorRepository, ClickHouseTelemetryRepository,
│   │                          # AuditRepository, InMemoryVectorRepository
│   └── streaming/             # RedpandaProducer (aiokafka producer)
│
└── presentation/              # Controllers & Transport Delivery
    ├── api/                   # FastAPI routers (troubleshoot_router, telemetry_router, health_router)
    ├── dependencies.py        # Dependency injection container & port binding
    └── websockets/            # WebSockets controllers (telemetry_ws: /ws/telemetry, /ws/troubleshoot)
```

---

## 4. Polyglot Persistence & Data Storage Architecture

| Data Engine | Role in VAT Platform | Primary Tables / Collections | Storage / Index Specs |
| :--- | :--- | :--- | :--- |
| **PostgreSQL 16** | Transactional state, audit records, and dense/sparse knowledge | `vendor_knowledge`<br>`troubleshooting_audit_ledger` | • HNSW Cosine Index (`vector_cosine_ops`)<br>• GIN Index on `tsvector`<br>• Row-Level Security (`FORCE RLS`) |
| **ClickHouse 24.3** | High-velocity analytical telemetry storage & aggregation | `vat.telemetry_raw`<br>`vat.telemetry_parsed` | • ReplacingMergeTree partitioned by day<br>• Kafka Engine automated ingestion tables |
| **Qdrant** | Distributed production vector search engine | `vat_vendor_knowledge` | • 384-dimensional cosine distance collection<br>• Fast ANN search with payload metadata filtering |
| **Redpanda** | Event streaming backbone (Kafka 3.4+ compatible) | Topics: `vat.telemetry.raw`, `vat.telemetry.parsed`, `vat.alerts` | • Low-latency C++ storage engine<br>• Consumer group offset tracking |
| **Redis** | Query caching and pub/sub notification | Cache keys: `vat:doc:*`, `vat:diag:*` | • In-memory key-value with TTL expiration<br>• Pub/Sub event broadcasting |
| **In-Memory Fallback** | Resilient air-gapped fallback corpus | `ENTERPRISE_FALLBACK_CORPUS` | • Embedded Python dictionary with pre-computed normalized 384-dim vectors |

---

## 5. Decoupled GPU Embedding Worker (`services/embedding_service`)

To prevent dense embedding generation from blocking the FastAPI event loop or competing for resources with web workers, embedding inference is isolated in a standalone microservice:

- **Location**: `services/embedding_service/main.py`
- **Network Port**: `8001`
- **Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 output dimensions, normalized L2 norm)
- **Endpoints**:
  - `POST /embed`: Accepts `List[str]`, returns `List[List[float]]`.
  - `GET /health`: Health and readiness probe.
  - `GET /metrics`: Prometheus latency and throughput metrics.
- **Resilience**: The backend client (`backend/infrastructure/ai/remote_embedding_client.py`) includes automatic retries and fails over to local in-process generation or deterministic vector hashing if the embedding service is unreachable.

---

## 6. Cloud-Native & Day-4 Infrastructure Architecture

The platform includes a comprehensive declarative Kubernetes suite (`k8s/`):

1. **Zero-Trust Service Mesh (Istio 1.22+)**:
   - Micro-segmented namespaces: `vat-redpanda`, `vat-vector`, `vat-embedding`, `vat-storage`, `vat-system`.
   - Global `STRICT` mTLS via `PeerAuthentication`.
   - Default-deny `AuthorizationPolicy` with SPIFFE principal whitelisting.

2. **Dynamic Secrets (HashiCorp Vault + External Secrets Operator)**:
   - Zero static database passwords stored in Git or environment variables.
   - `ClusterSecretStore` authenticates via Kubernetes Projected ServiceAccount Tokens.
   - Ephemeral database credentials rotated continuously on a 4-hour lease.

3. **FinOps & Compute Elasticity (KEDA + Karpenter)**:
   - KEDA 2.14+ `ScaledObject` monitors Redpanda consumer lag on `vat.telemetry.parsed`, scaling GPU embedding workers from **0 to 8 replicas** (scale-to-zero when queue is empty, eliminating idle GPU costs).
   - Karpenter v0.35+ schedules stateless workloads onto AWS Spot instances (`c6i`, `c7i`, `c6a`, `g4dn`, `g5`) with 30-second automated consolidation (~70% cost reduction), while preserving On-Demand multi-AZ quorums for stateful databases.

4. **Developer Experience (Loft vcluster + Tilt)**:
   - Lightweight virtual development clusters (<200MB RAM) running embedded k3s + SQLite.
   - Root `Tiltfile` enables sub-2-second live container sync directly into EKS without container rebuilds.

5. **Multi-Region Disaster Recovery (India Data Sovereignty)**:
   - **Primary Region**: AWS Mumbai (`ap-south-1`).
   - **Standby DR Region**: AWS Hyderabad (`ap-south-2`).
   - Redpanda MirrorMaker 2 replication with consumer offset checkpointing (RPO < 5s).
   - CloudNativePG PostgreSQL standby streaming replica with Barman S3 WAL replay fallback.
   - ClickHouse multi-region S3 zero-copy tiered storage & 5-node cross-region Keeper quorum.
   - Route53 ARC automated DNS failover with 10s health check intervals (RTO < 60s).

---

## 7. Explicit Scope Boundaries & Non-Implemented Features

To maintain absolute architectural integrity, the following components are explicitly defined as **NOT IMPLEMENTED / OUT OF SCOPE**:

- **Network Topology Graph Engine**: VAT does not construct or render network graph topologies, link-state databases, or CDP/LLDP neighbour graphs.
- **Path Trace / Hop-by-Hop Probe**: VAT does not calculate hop counts, hop latency, synthetic traceroute packets, or intermediate switch hops.
- **Active SNMP / gNMI Polling**: VAT does not actively poll network elements. It operates strictly as an event-driven passive consumer of telemetry streams.
- **Automated Direct-Device Push**: VAT does not connect to routers via SSH or Netconf to execute commands autonomously. All remediation playbooks are delivered to human engineers via 1-click copy, JSON export, and Markdown report formats with blast radius risk warnings.
