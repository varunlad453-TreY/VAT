# REST & WebSockets API Reference

**Canonical Specification for VAT Enterprise Backend & Decoupled Microservices**

- **FastAPI Core Service**: `http://localhost:8000`
- **Embedding Worker Microservice**: `http://localhost:8001`
- **Content-Type**: `application/json`
- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **OpenAPI JSON Specification**: `http://localhost:8000/openapi.json`

---

## 1. Diagnostic & Troubleshooting Endpoints (`/troubleshoot`)

### `POST /troubleshoot`
Analyzes multi-vendor error telemetry, queries hybrid vector search for official TAC manual citations, and synthesizes a structured 4-stage remediation runbook with blast radius risk scoring.

#### Request Body
```json
{
  "incident_id": "INC-8921",
  "device_id": "Edge-Router-East",
  "vendor": "cisco",
  "protocol": "bgp",
  "raw_logs": "%BGP-5-ADJCHANGE: neighbor 10.10.10.1 Down - BGP Notification sent, hold time expired",
  "context": {}
}
```

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `incident_id` | string | No | Optional incident identifier. Auto-generated if omitted. |
| `device_id` | string | Yes | Hostname or identifier of the impacted network device. |
| `vendor` | string | No | Vendor hint (`"cisco"`, `"juniper"`, `"velocloud"`, `"arista"`). Auto-detected if omitted. |
| `protocol` | string | No | Protocol hint (`"bgp"`, `"ospf"`, `"ipsec"`, `"evpn"`, `"interface"`). |
| `raw_logs` | string | Yes | Raw syslog or error message string. Minimum 1 character. |
| `context` | object | No | Additional diagnostic context key-value pairs. |

#### Response (200 OK)
```json
{
  "incident_id": "INC-8921",
  "generated_at": "2026-09-03T22:50:00Z",
  "vendor": "cisco",
  "protocol": "bgp",
  "diagnosis": "BGP Session Teardown: Router Edge-Router-East lost BGP peering with neighbor 10.10.10.1.",
  "root_cause_hypothesis": "Hold timer expired due to transit path keepalive packet drops or Path MTU blackholing.",
  "confidence_score": 0.96,
  "model_used": "deterministic-rag-synthesizer",
  "risk_assessment": {
    "risk_level": "HIGH",
    "estimated_downtime_sec": 30,
    "blast_radius_scope": "Single BGP Peer (neighbor 10.10.10.1)",
    "impacted_services": ["BGP Routing", "Prefix Exchange"]
  },
  "pre_checks": [
    {
      "step": 1,
      "command": "show ip bgp summary | include 10.10.10.1",
      "description": "Inspect current BGP state and hold timer negotiation",
      "expected_output": "State shows Active or Idle with 0 prefixes received"
    }
  ],
  "remediation_commands": [
    {
      "step": 1,
      "action": "Increase BGP Keepalive and Hold Timers",
      "command": "router bgp 65001\n neighbor 10.10.10.1 timers 30 90\n commit",
      "config_mode": "router bgp",
      "explanation": "Extends the hold time from default 180s to accommodate transient transit latency drops."
    }
  ],
  "post_checks": [
    {
      "step": 1,
      "command": "show ip bgp summary | include 10.10.10.1",
      "validation_criteria": "State transition to Established with active prefix count > 0"
    }
  ],
  "rollback_playbook": [
    {
      "step": 1,
      "action": "Restore standard carrier timers",
      "command": "router bgp 65001\n no neighbor 10.10.10.1 timers\n commit",
      "trigger_condition": "Neighbor remains in Idle or continuous state flapping persists > 60s"
    }
  ],
  "cited_vendor_docs": [
    {
      "source_url": "https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp/13753-25.html",
      "title": "Troubleshoot Common BGP Issues and Neighbor Reset",
      "vendor": "cisco",
      "similarity_score": 0.98,
      "excerpt": "BGP neighbor session reset. Causes: 1. Keepalive packets dropped..."
    }
  ]
}
```

---

### `GET /troubleshoot/sources`
Queries the indexed vendor documentation corpus matching keyword queries and metadata filters.

#### Query Parameters
- `query` (string, default: `"BGP neighbor reset hold time expired"`): Search terms.
- `vendor` (string, optional): Filter by vendor (`"cisco"`, `"juniper"`, `"velocloud"`, `"arista"`).
- `protocol` (string, optional): Filter by protocol (`"bgp"`, `"ospf"`, `"ipsec"`, `"evpn"`).
- `limit` (int, default: 5, min: 1, max: 20): Maximum number of citations to return.

#### Response (200 OK)
```json
[
  {
    "source_url": "https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp/13753-25.html",
    "title": "Troubleshoot Common BGP Issues and Neighbor Reset",
    "vendor": "cisco",
    "similarity_score": 0.98,
    "excerpt": "BGP neighbor session reset. Causes: 1. Keepalive packets dropped due to MTU mismatch..."
  }
]
```

---

### `GET /troubleshoot/audit`
Retrieves immutable historical troubleshooting executions from PostgreSQL `troubleshooting_audit_ledger`.

#### Query Parameters
- `limit` (int, default: 20, max: 100): Maximum number of records.
- `device_id` (string, optional): Filter by specific device hostname.

#### Response (200 OK)
```json
[
  {
    "id": 1,
    "incident_id": "INC-8921",
    "device_id": "Edge-Router-East",
    "vendor": "cisco",
    "risk_level": "HIGH",
    "diagnosis": "BGP Session Teardown",
    "created_at": "2026-09-03T22:50:00Z"
  }
]
```

---

## 2. Telemetry Ingestion Endpoints (`/telemetry`)

### `POST /telemetry/parse`
Parses an unstructured syslog string into a normalized `ParsedTelemetry` schema.

#### Request Body
```json
{
  "raw_log": "RP/0/RSP0/CPU0:Aug 26 12:45:00.123 : bgp[1050]: %ROUTING-BGP-5-ADJCHANGE : neighbor 10.10.10.1 Down",
  "device_hint": "Router-Agg-01"
}
```

#### Response (200 OK)
```json
{
  "raw_log": "RP/0/RSP0/CPU0:Aug 26 12:45:00.123 : bgp[1050]: %ROUTING-BGP-5-ADJCHANGE : neighbor 10.10.10.1 Down",
  "vendor": "cisco",
  "device_id": "Router-Agg-01",
  "event_code": "ROUTING-BGP-5-ADJCHANGE",
  "protocol": "bgp",
  "interface": null,
  "peer_ip": "10.10.10.1",
  "severity": "CRITICAL",
  "category": "routing",
  "extracted_keywords": ["bgp", "neighbor", "10.10.10.1", "down", "adjchange"]
}
```

---

### `POST /telemetry/ingest`
Batch ingests multiple telemetry entries with automatic RAG diagnostic triggering for high-severity events.

#### Request Body
```json
{
  "logs": [
    "%BGP-5-ADJCHANGE: neighbor 10.10.10.1 Down - BGP Notification sent",
    "Interface GigabitEthernet0/0/1 state changed to up"
  ],
  "auto_troubleshoot": true
}
```

#### Response (200 OK)
```json
{
  "total_received": 2,
  "parsed_events": [
    {
      "vendor": "cisco",
      "severity": "CRITICAL",
      "event_code": "BGP-5-ADJCHANGE",
      "protocol": "bgp"
    },
    {
      "vendor": "cisco",
      "severity": "INFO",
      "event_code": null,
      "protocol": "interface"
    }
  ],
  "troubleshooting_reports": [
    {
      "incident_id": "INC-AUTO-8921",
      "diagnosis": "BGP Session Teardown",
      "risk_assessment": { "risk_level": "HIGH" }
    }
  ]
}
```

---

## 3. Real-Time WebSockets Endpoints

### `WS /ws/telemetry`
Establishes a bi-directional real-time stream of incoming parsed telemetry events.
- **URL**: `ws://localhost:8000/ws/telemetry`
- **Protocol**: JSON WebSockets.
- **Server Push Payload**:
  ```json
  {
    "type": "TELEMETRY_EVENT",
    "timestamp": "2026-09-03T22:50:00Z",
    "device_id": "ASR9K-MUMBAI-01",
    "vendor": "cisco",
    "severity": "CRITICAL",
    "event_code": "ROUTING-BGP-5-ADJCHANGE",
    "protocol": "bgp",
    "raw_log": "..."
  }
  ```

### `WS /ws/troubleshoot`
Streams granular stage-by-stage progress updates during diagnostic synthesis.
- **URL**: `ws://localhost:8000/ws/troubleshoot`
- **Client Trigger**: Send `{"action": "START", "payload": <TroubleshootRequestDTO>}`
- **Server Stream Messages**:
  - `{"stage": "PARSING", "progress": 25, "message": "Normalizing vendor syslog tokens..."}`
  - `{"stage": "RETRIEVAL", "progress": 50, "message": "Executing dense-sparse vector RRF search..."}`
  - `{"stage": "SYNTHESIS", "progress": 75, "message": "Generating 4-stage playbook & blast radius..."}`
  - `{"stage": "COMPLETE", "progress": 100, "data": <TroubleshootResponseDTO>}`

---

## 4. Decoupled Embedding Worker API (Port 8001)

### `POST /embed`
Generates dense vector embeddings for input text batches.
- **URL**: `http://localhost:8001/embed`
- **Request Body**:
  ```json
  {
    "texts": ["BGP neighbor reset hold time expired", "OSPF MTU mismatch ExStart"]
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "embeddings": [
      [0.0123, -0.0456, ...],
      [-0.0789, 0.0321, ...]
    ],
    "dimensions": 384,
    "model": "all-MiniLM-L6-v2"
  }
  ```

### `GET /metrics`
Exports Prometheus monitoring metrics:
- `embedding_requests_total`: Cumulative embedding requests.
- `embedding_latency_seconds`: Histogram of inference processing latency.

---

## 5. Health & Diagnostic Probes

### `GET /health`
Returns backend health status, database pool connectivity, and active engine configurations:
```json
{
  "status": "healthy",
  "timestamp": "2026-09-03T22:50:00Z",
  "database_connected": true,
  "vector_dimensions": 384,
  "version": "2.0.0"
}
```

### `GET /`
Root endpoint returning platform metadata and canonical documentation links.
