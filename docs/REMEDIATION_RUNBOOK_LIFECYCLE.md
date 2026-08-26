# Remediation Runbook Lifecycle & Safety Architecture

**Canonical Specification of the 4-Stage Operational Model & Blast Radius Assessment**

---

## 1. The 4-Stage Carrier Remediation Model

To protect mission-critical carrier infrastructure from unplanned downtime, VAT enforces a strict 4-stage sequential runbook lifecycle:

```
┌────────────────────────────────────────────────────────────────────────────┐
│              STAGE 01: PRE-EXECUTION TELEMETRY VERIFICATION                │
│  • Constraint: Strictly READ-ONLY (No configuration modifications allowed) │
│  • Objective: Validate baseline failure conditions and current state        │
│  • Examples: show ip bgp summary, show ip ospf neighbor, ping do-not-frag  │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│              STAGE 02: TARGET CONFIGURATION REMEDIATION                    │
│  • Constraint: Deterministic syntax tailored to target vendor OS          │
│  • Objective: Apply exact configuration fix grounded in official TAC docs │
│  • Examples: ip mtu 1500, neighbor timers 30 90, reload-delay mlag 300     │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│              STAGE 03: POST-EXECUTION VERIFICATION & CONVERGENCE           │
│  • Constraint: Strict empirical convergence validation criteria            │
│  • Objective: Prove route table stabilization and packet recovery          │
│  • Criteria: Prefix count > 0, Packet loss < 0.5%, Adjacency = FULL        │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │
                         ┌────────────┴────────────┐
                         │ Validation Successful? │
                         └────────────┬────────────┘
                                      │
                        ┌─────────────┴─────────────┐
                        │ YES                       │ NO / Convergence Timeout
                        ▼                           ▼
            ┌───────────────────────┐   ┌────────────────────────────────────┐
            │  INCIDENT RESOLVED    │   │ STAGE 04: SAFE ROLLBACK PLAYBOOK   │
            │  • Record audit entry │   │ • Undo applied config changes      │
            │  • Close ticket       │   │ • Restore original stable baseline │
            └───────────────────────┘   └────────────────────────────────────┘
```

---

## 2. Blast Radius & Operational Risk Classification

Every synthesized playbook includes an automated `RiskAssessment` object:

```python
class RiskAssessment(BaseModel):
    risk_level: str               # 'LOW', 'MEDIUM', 'HIGH'
    estimated_downtime_sec: int   # Anticipated transition time (e.g. 0 to 60s)
    blast_radius_scope: str       # 'Single Interface / Peer', 'Local Spine', 'Transit AS'
    impacted_services: List[str]  # ['BGP Peering', 'Overlay VCMP Tunnels', 'EVPN VXLAN']
```

### Risk Level Criteria:
- **`LOW` (Non-Disruptive)**: MTU adjustment on non-forwarding interface, timer parameter changes that take effect on next cycle without resetting adjacency.
- **`MEDIUM` (Transient Convergence)**: Protocol restart, clearing OSPF process, BGP soft-reconfiguration (`clear ip bgp soft`).
- **`HIGH` (Service Disruption / Route Flap)**: Interface bounce (`shutdown` $\rightarrow$ `no shutdown`), MLAG reload delay activation, hard peer reset.

---

## 3. Rollback Playbook Specifications

A rollback step is **mandatory** for every Stage 02 configuration command. Each rollback step defines:
- **Exact Reversion Command**: Syntax to undo the specific change (`no neighbor ...`, `rollback 0`, `revert profile`).
- **Explicit Trigger Condition**: Precise failure conditions that mandate immediate execution (e.g. *"Neighbor remains in Idle state or continuous flapping persists > 60 seconds after commit"*).
