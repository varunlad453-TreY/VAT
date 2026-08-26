# Platform Status, Limitations & Engineering Roadmap

**Canonical Source of Truth for Feature Status, Technical Debt, and Product Roadmap**

---

## 1. Feature Implementation Matrix

| Feature Area | Current Status | Description & Grounded Verification |
| :--- | :--- | :--- |
| **Multi-Vendor Telemetry Normalization** | **IMPLEMENTED** | Regex-based parser for Cisco (IOS-XE/XR), Juniper (Junos), VMware VeloCloud SD-WAN, and Arista (EOS). |
| **Hybrid Vector Search Engine** | **IMPLEMENTED** | pgvector HNSW Cosine Similarity (65%) + PostgreSQL tsvector GIN BM25 (35%) with Reciprocal Rank Fusion. |
| **4-Stage Remediation Playbook Engine** | **IMPLEMENTED** | Generates Pre-Checks (Read-Only), Target Configuration CLI, Post-Checks, and Safe Rollbacks. |
| **Operational Risk & Blast Radius Assessment** | **IMPLEMENTED** | Computes risk level (`LOW`, `MEDIUM`, `HIGH`), estimated downtime seconds, and impacted services. |
| **Air-Gapped Offline Fallback Mode** | **IMPLEMENTED** | Operates with 100% functionality even when PostgreSQL or cloud LLM APIs are disconnected. |
| **NOC Console Split-Pane Canvas** | **IMPLEMENTED** | Canvas-based high-density UI with zero emojis, zero card-grids, real-time UTC clock, and incident presets. |
| **Runbook Export Suite** | **IMPLEMENTED** | Copy Full CLI Script, Export JSON Runbook, and Export Markdown Incident Report. |
| **Permanent Audit Ledger** | **IMPLEMENTED** | PostgreSQL `troubleshooting_audit_ledger` with async query and JSONB history. |
| **External LLM Cloud Inference** | **IMPLEMENTED** | Supports OpenAI / Azure / GitHub Models API via `AsyncOpenAI` JSON mode (optional via API key). |
| **Live Network Discovery / SNMP Polling** | **NOT IMPLEMENTED** | System operates on received syslogs and telemetry payloads; does not perform active SNMP/gNMI device polling. |
| **Automated Direct-Device Execution** | **NOT IMPLEMENTED** | Commands are synthesized with 1-click copy/export; direct Netconf/SSH automated execution on physical routers is planned for Phase 3. |
| **Path Trace / Network Topology Graph** | **NOT IMPLEMENTED** | Not in current architectural scope (VAT is a multi-vendor RAG diagnostic & remediation engine). |
| **WiFi AP Floorplan Visualizer** | **NOT IMPLEMENTED** | Out of domain scope. |
| **User Authentication / RBAC (OIDC/SAML)** | **NOT IMPLEMENTED** | Endpoints are open NOC REST routes ready for API Gateway / reverse-proxy authentication. |

---

## 2. Known Limitations & Technical Debt

1. **In-Memory Fallback Corpus Size**: The offline fallback corpus currently contains pre-indexed troubleshooting playbooks for 5 major failure modes across Cisco, Juniper, VeloCloud, and Arista. For production scale across thousands of obscure vendor bugs, the PostgreSQL `vendor_knowledge` table must be seeded with full manual corpora via `scripts/ingest_vendor_docs.py`.
2. **Direct CLI Execution Safety Gate**: Currently, the platform relies on engineer confirmation and 1-click copy rather than direct SSH/Netconf execution to prevent accidental production outages.
3. **Database Connection Retry Policy**: When starting up without PostgreSQL, the connection pool defers gracefully, but dynamic background reconnect attempts could be enhanced with an exponential backoff loop.

---

## 3. Product Roadmap

### Completed (Phase 1 & Phase 2)
- [x] Multi-Vendor Syslog Normalizer & Tokenizer
- [x] Hybrid Dense (pgvector HNSW) + Sparse (tsvector GIN) Search Pipeline
- [x] Deterministic 4-Stage Operational Remediation Model (Pre-Check $\rightarrow$ Fix $\rightarrow$ Post-Check $\rightarrow$ Rollback)
- [x] Operational Risk & Blast Radius Classifier
- [x] High-Density Enterprise NOC Console UI (Eradication of card-grid and emojis)
- [x] Runbook Export Engine (CLI Script, JSON, Markdown)
- [x] Full Pytest Suite (25/25 Passing)

### Planned (Phase 3: Automated Netconf & Carrier Integration)
- [ ] **Netconf / gNMI Push-to-Device Integration**: Direct execution of validated remediation commands with pre-execution safety gates.
- [ ] **ServiceNow & Jira Service Desk Webhook Connector**: Automated ticket creation and bidirectional status synchronization.
- [ ] **Expanded Multi-Vendor Knowledge Bases**: Adding Nokia SR OS, Huawei VRP, and Fortinet FortiOS manuals to the ingestion pipeline.
- [ ] **OIDC / Enterprise Single Sign-On (SSO)**: Role-Based Access Control (RBAC) separating L1 Helpdesk operators from L3 TAC engineers.
- [ ] **Live Telemetry WebSockets Stream**: Real-time push stream from Kafka / Fluentd aggregators.
