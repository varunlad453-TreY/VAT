"""
Enterprise Remediation, Blast Radius & Audit Ledger Models (VAT Phase 2)
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PreCheckCommand(BaseModel):
    """Read-only diagnostic inspection command to run before making changes."""
    step: int = 1
    command: str = Field(..., description="Exact read-only CLI command (e.g. 'show ip bgp summary')")
    description: str = Field(..., description="Purpose of the inspection")
    expected_output: str = Field(..., description="Expected diagnostic observation")


class RemediationCommand(BaseModel):
    """Configuration or operational fix command."""
    step: int = 1
    action: str = Field(..., description="Remediation action summary")
    command: str = Field(..., description="Exact CLI configuration or operational syntax")
    config_mode: str = Field(default="interface", description="Target configuration mode ('interface', 'router bgp', 'set', etc.)")
    explanation: str = Field(..., description="Technical rationale grounded in official vendor documentation")


class PostCheckCommand(BaseModel):
    """Validation query executed to empirically confirm service restoration."""
    step: int = 1
    command: str = Field(..., description="Validation query command")
    validation_criteria: str = Field(..., description="Verification condition (e.g. 'Adjacency state equals FULL')")


class RollbackCommand(BaseModel):
    """Safe reversion command in case post-check validation fails."""
    step: int = 1
    action: str = Field(..., description="Rollback action")
    command: str = Field(..., description="Exact CLI command to restore previous operational state")
    trigger_condition: str = Field(..., description="Condition requiring rollback")


class RiskAssessment(BaseModel):
    """Blast radius and operational risk classification."""
    risk_level: str = Field(default="LOW", description="'LOW' (non-disruptive), 'MEDIUM' (protocol restart), 'HIGH' (interface bounce / route flap)")
    estimated_downtime_sec: int = Field(default=0, description="Estimated service disruption time in seconds")
    blast_radius_scope: str = Field(default="Single Interface / Peer", description="Scope of impact")
    impacted_services: List[str] = Field(default_factory=list, description="Services potentially affected during remediation")


class AuditLedgerEntry(BaseModel):
    """Permanent audit record of executed troubleshooting session."""
    id: Optional[int] = None
    incident_id: Optional[str] = None
    device_id: str
    vendor: str
    raw_logs: str
    diagnosis: str
    root_cause: str
    risk_level: str
    remediation_steps: List[Dict[str, Any]] = Field(default_factory=list)
    rollback_steps: List[Dict[str, Any]] = Field(default_factory=list)
    cited_sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_score: float = 0.95
    model_used: str = "deterministic-rag-synthesizer"
    executed_by: str = "noc_operator"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
