# REST API Reference & Endpoint Specification

**Canonical API Reference for VAT Enterprise Backend**

- **Base URL**: `http://localhost:8000`
- **Content-Type**: `application/json`
- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## 1. Diagnostic & Troubleshooting Endpoints

### `POST /troubleshoot`
Analyzes multi-vendor error telemetry, executes hybrid search against vendor documentation, and generates a structured 4-stage remediation runbook.

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

#### Response (200 OK)
```json
{
  "incident_id": "INC-8921",
  "generated_at": "2026-08-26T12:46:00Z",
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
Retrieves indexed vendor manual chunks matching query, vendor, and protocol filters.

#### Query Parameters
- `query` (string, default: `"BGP neighbor reset hold time expired"`): Search keywords.
- `vendor` (string, optional): `"cisco"`, `"juniper"`, `"velocloud"`, or `"arista"`.
- `protocol` (string, optional): `"bgp"`, `"ospf"`, `"ipsec"`, `"evpn"`.
- `limit` (integer, default: 5, min: 1, max: 20): Maximum citations to return.

#### Response (200 OK)
```json
[
  {
    "source_url": "https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp/13753-25.html",
    "title": "Troubleshoot Common BGP Issues and Neighbor Reset",
    "vendor": "cisco",
    "similarity_score": 0.98,
    "excerpt": "BGP neighbor session reset..."
  }
]
```

---

### `GET /troubleshoot/audit`
Fetches recent permanent troubleshooting and remediation audit log records from PostgreSQL.

#### Query Parameters
- `limit` (integer, default: 20, min: 1, max: 100): Number of audit records.
- `vendor` (string, optional): Filter by vendor name.

#### Response (200 OK)
```json
[
  {
    "id": 104,
    "incident_id": "INC-8921",
    "device_id": "Edge-Router-East",
    "vendor": "cisco",
    "diagnosis": "BGP Session Teardown...",
    "risk_level": "HIGH",
    "remediation_steps": [...],
    "rollback_steps": [...],
    "confidence_score": 0.96,
    "created_at": "2026-08-26T12:46:00Z"
  }
]
```

---

## 2. Telemetry Ingestion Endpoints

### `POST /telemetry/parse`
Parses a single raw syslog line and returns normalized event metadata.

#### Query Parameters
- `raw_log` (string, required): Raw syslog line.
- `device_hint` (string, optional): Device hostname hint.

#### Response (200 OK)
```json
{
  "raw_log": "%BGP-5-ADJCHANGE: neighbor 10.10.10.1 Down",
  "vendor": "cisco",
  "device_id": "Core-Router-01",
  "event_code": "%BGP-5-ADJCHANGE",
  "protocol": "bgp",
  "interface": null,
  "peer_ip": "10.10.10.1",
  "severity": "CRITICAL",
  "category": "routing",
  "extracted_keywords": ["bgp", "10.10.10.1", "%BGP-5-ADJCHANGE"]
}
```

---

### `POST /telemetry/ingest`
Ingests a batch of syslog messages with optional automated RAG troubleshooting for actionable errors.

#### Request Body
```json
{
  "logs": [
    "%BGP-5-ADJCHANGE: neighbor 10.10.10.1 Down - BGP Notification sent, hold time expired",
    "rpd[1234]: RPD_BGP_NEIGHBOR_STATE_CHANGED: BGP peer 172.16.1.1 changed state to Idle"
  ],
  "device_hint": "Core-Router-01",
  "auto_troubleshoot": true
}
```

#### Response (200 OK)
```json
{
  "total_received": 2,
  "parsed_events": [...],
  "troubleshooting_reports": [...]
}
```

---

## 3. System & Health Endpoints

### `GET /health`
Probes service health, version, and PostgreSQL database connectivity.

#### Response (200 OK)
```json
{
  "status": "healthy",
  "service": "vendor-aware-troubleshooter-enterprise",
  "database_connected": true,
  "version": "2.0.0",
  "timestamp": "2026-08-26T12:46:00Z"
}
```

---

### `GET /console`
Directly serves the high-density NOC console web interface (`index.html`).
