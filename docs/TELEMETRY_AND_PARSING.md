# Multi-Vendor Telemetry & Syslog Parsing Specification

**Canonical Reference for Regex Normalization and Token Extraction**

---

## 1. Overview & Objectives

The telemetry parsing engine is implemented in `backend/infrastructure/adapters/telemetry_parser_adapter.py` (and legacy service `backend/services/telemetry_parser.py`). It normalizes unstructured carrier syslog streams into a strongly-typed `ParsedTelemetry` domain entity:

```python
class ParsedTelemetry(BaseModel):
    raw_log: str
    vendor: str            # 'cisco', 'juniper', 'velocloud', 'arista', 'generic'
    device_id: str         # Extracted hostname
    event_code: Optional[str]
    protocol: Optional[str]# 'bgp', 'ospf', 'ipsec', 'evpn', 'interface'
    interface: Optional[str]
    peer_ip: Optional[str]
    severity: str          # 'CRITICAL', 'ERROR', 'WARNING', 'INFO'
    category: str          # 'routing', 'switching', 'sdwan', 'hardware'
    extracted_keywords: List[str]
```

---

## 2. Ingestion Pipeline & Vector Syslog Daemon

Telemetry arrives through two primary ingress pathways:
1. **Asynchronous Syslog Pipeline**: Carrier edge routers ship RFC 5424 / RFC 3164 syslog packets over UDP/TCP port 514 to the **Vector DaemonSet** (`k8s/vector/daemonset.yaml`). Vector tags the stream with ingest timestamps and forwards events to the Redpanda broker topic `vat.telemetry.raw`.
2. **Synchronous REST API**: External aggregators or NOC engineers submit syslogs directly via `POST /telemetry/parse` or `POST /telemetry/ingest`.

---

## 3. Multi-Vendor Regex Recognition Matrix

### 3.1 Cisco Systems (IOS-XE / IOS-XR)
- **Signature Pattern**: `r'(%[A-Z0-9_]+-[0-9]+-[A-Z0-9_]+)'`
- **Supported Event Codes**:
  - `%BGP-5-ADJCHANGE`: BGP neighbor state transition (Established to Down).
  - `%OSPF-5-ADJCHG`: OSPF neighbor adjacency change (EXSTART, INIT, DOWN).
  - `%LINK-3-UPDOWN` & `%LINEPROTO-5-UPDOWN`: Physical / data-link interface state changes.
- **Interface Patterns**: `GigabitEthernet\d+`, `TenGigabitEthernet\d+`, `FastEthernet\d+`.

### 3.2 Juniper Networks (Junos OS)
- **Signature Patterns**: `rpd[`, `RPD_`, `SNMP_TRAP_`, `KMD_VPN_`, `CHASSISD_`, `alarmd[`.
- **Supported Event Codes**:
  - `RPD_BGP_NEIGHBOR_STATE_CHANGED`: Junos BGP routing daemon state change.
  - `KMD_VPN_DOWN`: IPsec / VPN tunnel renegotiation failure.
- **Interface Patterns**: `ge-\d+/\d+/\d+`, `xe-\d+/\d+/\d+`, `et-\d+/\d+/\d+`.

### 3.3 VMware VeloCloud SD-WAN
- **Signature Patterns**: `velocloud`, `velobrain`, `vcmp`, `tunnel_dead`, `qoe_drop`, `pmtud`.
- **Supported Event Codes**:
  - `EDGE_LINK_DEGRADATION`: WAN link packet loss or jitter exceeding carrier SLA.
  - `PMTUD_BLACKHOLE`: Underlay MTU fragmentation dropping VCMP UDP 2426 packets.
  - `TUNNEL_DEAD`: Complete gateway reachability timeout.

### 3.4 Arista Networks (EOS)
- **Signature Patterns**: `%MLAG-`, `%VXLAN-`, `%EVPN-`, `Arista`.
- **Supported Event Codes**:
  - `%MLAG-4-SPLIT_BRAIN`: Multi-Chassis Link Aggregation peer-link failure with secondary node isolation.
  - `%VXLAN-4-PORT_VLAN`: VXLAN tunnel endpoint encapsulation drops.
- **Interface Patterns**: `Ethernet\d+/\d+`, `Port-Channel\d+`.

---

## 4. Severity & Protocol Mapping Rules

| Raw Keywords | Mapped Severity | Action Trigger |
| :--- | :--- | :--- |
| `down`, `dead`, `reset`, `expired`, `split_brain`, `fail`, `fatal` | **`CRITICAL`** | Automatically triggers RAG troubleshooting runbook synthesis |
| `error`, `degraded`, `retransmission`, `mismatch`, `loss` | **`ERROR`** | Automatically triggers RAG troubleshooting runbook synthesis |
| `warning`, `flap`, `timeout` | **`WARNING`** | Normalized and ingested into ClickHouse analytics |
| `up`, `established`, `recovered` | **`INFO`** | Normalized and ingested into ClickHouse analytics |
