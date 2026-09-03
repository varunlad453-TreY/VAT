# Testing & Quality Assurance Architecture

**Canonical Specification of the Test Suite, Coverage Metrics & CI/CD Gates**

---

## 1. Overview & Testing Philosophy

The VAT Enterprise test suite is engineered for zero-defect carrier operations. It enforces:

1. **Air-Gapped Resilient Verification**: Tests validate both primary clustered integrations (PostgreSQL, ClickHouse, Qdrant, Redpanda) and graceful in-memory fallbacks when external services are disconnected.
2. **Deterministic Output Assertions**: Remediation playbooks, risk levels, and CLI commands are strictly validated for TAC manual alignment and zero-hallucination syntax.
3. **Continuous Integration Verification**: Every commit is verified via GitHub Actions (`.github/workflows/ci.yaml`) executing linting, static schema validation, and the full Pytest suite.

---

## 2. Test Suite Inventory (75 Passing Tests)

The repository contains **75 automated tests** organized across 10 specialized modules in `tests/`:

```
tests/
├── test_action3_load_pipeline.py           # 2 Tests: ClickHouse Kafka schemas & BGP storm generator
├── test_chaos_engineering.py               # 3 Tests: Chaos Mesh pod kills, partitions & schedules
├── test_embedding_service.py               # 6 Tests: Decoupled microservice, metrics & client retries
├── test_enterprise_multivendor.py          # 14 Tests: Multi-vendor parsers, hybrid search & 4-stage lifecycle
├── test_gitops_pipeline.py                 # 3 Tests: CI/CD workflows and ArgoCD ApplicationSets
├── test_ingestion_pipeline.py              # 2 Tests: Redpanda consumer loop & Vector config validation
├── test_phase3_infrastructure.py           # 19 Tests: Clean architecture adapters, DI ports & fallback repos
├── test_phase4_presentation_websockets.py  # 11 Tests: REST presentation controllers & WebSockets streams
├── test_polyglot_persistence.py            # 2 Tests: ClickHouse & Qdrant repository fallback mechanics
└── test_vendor_rag_troubleshooter.py       # 9 Tests: Text chunking, pgvector HNSW & baseline RAG endpoints
```

### Granular Module Breakdown

| Test Module | Test Class / Functions | Functional Verification Scope |
| :--- | :--- | :--- |
| `test_enterprise_multivendor.py` | `TestTelemetryParserService`<br>`TestMultiVendorHybridSearch`<br>`TestEnterpriseRemediationLifecycle`<br>`TestEnterpriseTelemetryAPI` | Validates regex normalization for Cisco, Juniper, VeloCloud, and Arista; tests dense-sparse RRF search; verifies 4-stage runbook synthesis and blast radius scoring. |
| `test_phase3_infrastructure.py` | `TestVectorRepositories`<br>`TestAuditRepository`<br>`TestTelemetryParserAdapter`<br>`TestAISynthesizers`<br>`TestRedisCacheService`<br>`TestApplicationUseCases` | Validates Hexagonal architecture use cases, port interfaces, in-memory fallback corpus, SHA-256 normalized embeddings, and Redis caching. |
| `test_phase4_presentation_websockets.py` | `TestPresentationRESTControllers`<br>`TestDependencyInjectionOverrides`<br>`TestPresentationWebSockets` | Validates FastAPI presentation routers (`/troubleshoot`, `/telemetry/*`, `/health`), DI container overrides, and real-time WebSockets streaming (`/ws/telemetry`, `/ws/troubleshoot`). |
| `test_embedding_service.py` | `TestEmbeddingMicroservice`<br>`TestRemoteEmbeddingClient` | Validates decoupled FastAPI embedding microservice on port 8001, `/embed` batch contract, Prometheus metrics (`/metrics`), and client retry fallbacks. |
| `test_polyglot_persistence.py` | `test_clickhouse_telemetry_repository_fallback`<br>`test_qdrant_vector_repository_search_fallback` | Validates graceful degradation and offline fallbacks for ClickHouse analytics and Qdrant vector storage. |
| `test_vendor_rag_troubleshooter.py` | `TestVectorEmbeddingAndChunking`<br>`TestVectorService`<br>`TestAIServiceRAGSynthesis`<br>`TestFastAPIEndpoints` | Validates text chunking with sliding window overlap, pgvector HNSW retrieval, and baseline diagnostic endpoints. |
| `test_chaos_engineering.py` | `test_redpanda_pod_kill_manifest`<br>`test_clickhouse_network_partition_manifest`<br>`test_chaos_schedule_workflow_manifest` | Validates declarative Chaos Mesh CRD manifests and resilience schedule configurations. |
| `test_gitops_pipeline.py` | `test_github_actions_ci_workflow`<br>`test_github_actions_deploy_workflow`<br>`test_argocd_appset_manifest` | Validates GitHub Actions workflow YAML syntax, step dependencies, and ArgoCD ApplicationSet generators. |
| `test_ingestion_pipeline.py` | `test_redpanda_consumer_lifecycle`<br>`test_vector_config_exists_and_valid` | Validates Redpanda consumer group commit loop and Vector syslog daemon configurations. |
| `test_action3_load_pipeline.py` | `test_clickhouse_kafka_engine_sql_schema`<br>`test_bgp_storm_batch_generator` | Validates ClickHouse Kafka engine DDL and BGP telemetry burst generator script. |

---

## 3. Running Tests Locally

### Run Entire Test Suite
```bash
pytest tests/ -v
```

### Run Specific Test Modules
```bash
# Test Decoupled Embedding Worker:
pytest tests/test_embedding_service.py -v

# Test WebSockets and REST Controllers:
pytest tests/test_phase4_presentation_websockets.py -v

# Test Multi-Vendor Parsing & Runbook Synthesis:
pytest tests/test_enterprise_multivendor.py -v

# Test Polyglot Persistence & Resilience Fallbacks:
pytest tests/test_polyglot_persistence.py -v
```

### Run with Execution Timing & Fail-Fast
```bash
pytest tests/ --durations=10 -x
```

---

## 4. Test Distinction: Functional vs. Resilient Fallback

To maintain rigorous software integrity, the test suite explicitly separates tests that validate clustered infrastructure from tests that validate air-gapped fallback mechanics:

- **Clustered Integration Tests**: Validate actual SQL queries, Kafka consumers, and vector distance operations against running Docker containers or Kubernetes services.
- **Graceful Fallback Tests**: Validate that when external dependencies are intentionally disconnected or unreachable, the system executes cleanly using `ENTERPRISE_FALLBACK_CORPUS`, `InMemoryVectorRepository`, and `DeterministicSynthesizer` without raising uncaught exceptions or dropping incoming telemetry.

---

## 5. CI/CD Automated Test Gates

All pull requests and merges to `main` trigger `.github/workflows/ci.yaml`:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --junitxml=test-results.xml
```

A build cannot merge unless **100% of the 75 automated tests pass**.
