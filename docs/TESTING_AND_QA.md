# Testing & Quality Assurance Architecture

**Canonical Specification of Test Suites, Coverage & Validation Rules**

---

## 1. Test Architecture Overview

VAT maintains a comprehensive automated test suite across unit, integration, RAG synthesis, and API contract layers.

- **Test Framework**: `pytest` + `pytest-asyncio` + `httpx` (`TestClient`).
- **Execution Command**:
  ```powershell
  pytest tests/ -v
  ```
- **Current Test Results**: **25 passed in 0.91s** (100% pass rate).

---

## 2. Test Suite Matrix

### 2.1 `tests/test_vendor_rag_troubleshooter.py` (Core RAG & Unit Suite)
| Test Class | Test Case | Scope & Verification |
| :--- | :--- | :--- |
| `TestVectorEmbeddingAndChunking` | `test_text_chunking_with_overlap` | Verifies 400-word chunking and 50-word overlap preservation. |
| | `test_vector_embedding_dimension` | Verifies 384-dimensional normalized vector output ($\|\mathbf{v}\| \approx 1.0$). |
| `TestVectorService` | `test_find_relevant_docs_fallback_corpus` | Tests in-memory vector similarity retrieval for OSPF EXSTART. |
| | `test_find_relevant_docs_with_mocked_db` | Tests asyncpg database query execution with mocked pgvector connection. |
| `TestAIServiceRAGSynthesis` | `test_suggest_resolution_ospf_exstart_issue` | Validates end-to-end RAG synthesis, confidence score $\ge 0.85$, and Cisco TAC citations. |
| `TestFastAPIEndpoints` | `test_health_check_endpoint` | Probes `/health` status. |
| | `test_root_endpoint` | Verifies `/` metadata endpoints. |
| | `test_troubleshoot_endpoint_success` | Tests `/troubleshoot` with valid Cisco OSPF log. |
| | `test_troubleshoot_endpoint_validation_error` | Tests HTTP 422 error rejection on empty log payloads. |
| | `test_list_vendor_sources_endpoint` | Tests `/troubleshoot/sources` vector query filter. |

---

### 2.2 `tests/test_enterprise_multivendor.py` (Multi-Vendor Integration Suite)
| Test Class | Test Case | Scope & Verification |
| :--- | :--- | :--- |
| `TestTelemetryParserService` | `test_cisco_bgp_parser` | Validates Cisco BGP event extraction (`%BGP-5-ADJCHANGE`, peer `10.10.10.1`, severity `CRITICAL`). |
| | `test_juniper_bgp_parser` | Validates Junos `RPD_BGP_NEIGHBOR_STATE_CHANGED` extraction. |
| | `test_velocloud_sdwan_parser` | Validates VeloCloud SD-WAN `EDGE_LINK_DEGRADATION`, interface `GE3`, severity `ERROR`. |
| | `test_arista_mlag_parser` | Validates Arista EOS `%MLAG-4-SPLIT_BRAIN` extraction and severity `CRITICAL`. |
| `TestMultiVendorHybridSearch` | `test_hybrid_search_cisco_bgp` | Tests hybrid search filtering for Cisco BGP. |
| | `test_hybrid_search_juniper_junos` | Tests hybrid search filtering for Juniper Junos. |
| | `test_hybrid_search_velocloud_pmtud` | Tests hybrid search filtering for VeloCloud SD-WAN. |
| | `test_hybrid_search_arista_mlag` | Tests hybrid search filtering for Arista EOS. |
| `TestEnterpriseRemediationLifecycle` | `test_cisco_bgp_remediation_generation` | Validates 4-stage generation (Pre-checks, Fixes, Post-checks, Rollbacks). |
| | `test_arista_mlag_split_brain_high_risk` | Validates Arista MLAG split-brain classification as `HIGH` risk with `reload-delay`. |
| `TestEnterpriseTelemetryAPI` | `test_parse_endpoint` | Validates `/telemetry/parse` HTTP endpoint. |
| | `test_batch_ingest_with_auto_troubleshoot` | Validates `/telemetry/ingest` batch stream with auto-RAG triggering. |
| | `test_audit_history_endpoint` | Validates `/troubleshoot/audit` query endpoint. |
| | `test_console_endpoint` | Validates `/console` serves valid NOC HTML. |
| | `test_console_slash_endpoint` | Validates `/console/` trailing-slash redirect/route. |
