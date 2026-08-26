"""
Domain Entity: 4-Stage Remediation Runbook & Risk Assessment
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.domain.enums import RiskLevel, ConfigMode


class PreCheckCommand(BaseModel):
    """Stage 1: Read-only non-destructive diagnostic command."""
    step: int = 1
    command: str = Field(..., description="Exact read-only CLI command (e.g. 'show ip bgp summary')")
    description: str = Field(..., description="Purpose of the state inspection")
    expected_output: str = Field(..., description="Expected diagnostic observation")


class RemediationCommand(BaseModel):
    """Stage 2: Deterministic configuration or operational fix command."""
    step: int = 1
    action: str = Field(..., description="Summary of the remediation action")
    command: str = Field(..., description="Exact CLI configuration or operational syntax")
    config_mode: str = Field(default=ConfigMode.INTERFACE.value, description="Target configuration mode")
    explanation: str = Field(..., description="Technical rationale grounded in official vendor docs")


class PostCheckCommand(BaseModel):
    """Stage 3: Validation query executed to empirically confirm service restoration."""
    step: int = 1
    command: str = Field(..., description="Validation query command")
    validation_criteria: str = Field(..., description="Empirical verification condition")


class RollbackCommand(BaseModel):
    """Stage 4: Safe reversion command in case post-check validation fails."""
    step: int = 1
    action: str = Field(..., description="Rollback action summary")
    command: str = Field(..., description="Exact CLI command to restore previous stable state")
    trigger_condition: str = Field(..., description="Precise trigger condition requiring rollback")


class RiskAssessment(BaseModel):
    """Blast radius and operational risk classification."""
    risk_level: str = Field(default=RiskLevel.LOW.value, description="Operational risk level")
    estimated_downtime_sec: int = Field(default=0, description="Estimated transition downtime in seconds")
    blast_radius_scope: str = Field(default="Single Interface / Peer", description="Scope of network impact")
    impacted_services: List[str] = Field(default_factory=list, description="Services potentially affected")


class RemediationRunbook(BaseModel):
    """Complete 4-stage operational remediation runbook entity."""
    runbook_id: Optional[str] = None
    vendor: str
    protocol: str
    diagnosis: str
    root_cause_hypothesis: str
    confidence_score: float = 0.90
    risk_assessment: RiskAssessment = Field(default_factory=RiskAssessment)
    pre_checks: List[PreCheckCommand] = Field(default_factory=list)
    remediation_commands: List[RemediationCommand] = Field(default_factory=list)
    post_checks: List[PostCheckCommand] = Field(default_factory=list)
    rollback_playbook: List[RollbackCommand] = Field(default_factory=list)
