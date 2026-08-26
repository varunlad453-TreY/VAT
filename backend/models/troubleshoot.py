"""
Pydantic Models for Vendor-Aware Troubleshooting (VAT Phase 2)
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.models.remediation import (
    PostCheckCommand,
    PreCheckCommand,
    RemediationCommand,
    RiskAssessment,
    RollbackCommand,
)


class VendorDocCitation(BaseModel):
    """Citation of retrieved vendor documentation chunk."""
    source_url: str = Field(..., description="Official vendor documentation URL")
    title: str = Field(..., description="Document title")
    vendor: str = Field(default="cisco", description="Hardware/Software vendor")
    similarity_score: float = Field(..., description="Cosine / Hybrid similarity score (0.0 to 1.0)")
    excerpt: str = Field(..., description="Relevant knowledge snippet from vendor manual")


class TroubleshootRequest(BaseModel):
    """Input request for troubleshooting analysis."""
    incident_id: Optional[str] = Field(default=None, description="Optional incident ID if available")
    device_id: Optional[str] = Field(default=None, description="Target device hostname or IP")
    vendor: Optional[str] = Field(default=None, description="Target device vendor ('cisco', 'juniper', 'velocloud', 'arista')")
    protocol: Optional[str] = Field(default=None, description="Optional target protocol filter ('bgp', 'ospf', 'evpn', etc.)")
    raw_logs: str = Field(..., description="Raw syslog, CLI output, or telemetry error log message")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional telemetry context")


class ResolutionStep(BaseModel):
    """Legacy backward-compatible step structure."""
    step_number: int = Field(..., description="Sequential step number")
    action: str = Field(..., description="Action summary")
    command: Optional[str] = Field(default=None, description="Exact vendor CLI command to run")
    expected_output: Optional[str] = Field(default=None, description="Expected command output or validation check")
    explanation: str = Field(..., description="Technical rationale grounded in vendor manual")


class TroubleshootResponse(BaseModel):
    """Enterprise AI troubleshooting resolution playbook."""
    incident_id: Optional[str] = Field(default=None, description="Associated incident ID")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Generation timestamp")
    vendor: str = Field(default="cisco", description="Target vendor")
    protocol: str = Field(default="general", description="Detected protocol")
    diagnosis: str = Field(..., description="Executive summary of the detected failure mode")
    root_cause_hypothesis: str = Field(..., description="Technical root cause identified from live data")
    confidence_score: float = Field(..., description="Diagnostic confidence score (0.0 to 1.0)")
    model_used: str = Field(default="deterministic-rag-synthesizer", description="LLM model used for synthesis")
    
    # 3-Stage Enterprise Remediation Lifecycle
    pre_checks: List[PreCheckCommand] = Field(default_factory=list, description="Read-only diagnostic checks")
    remediation_commands: List[RemediationCommand] = Field(default_factory=list, description="Exact CLI configuration remediation commands")
    post_checks: List[PostCheckCommand] = Field(default_factory=list, description="Validation queries verifying recovery")
    rollback_playbook: List[RollbackCommand] = Field(default_factory=list, description="Safe rollback instructions if validation fails")
    risk_assessment: RiskAssessment = Field(default_factory=RiskAssessment, description="Blast radius & operational risk assessment")
    
    # Backward compatibility
    resolution_steps: List[ResolutionStep] = Field(default_factory=list, description="Legacy resolution list")
    cited_vendor_docs: List[VendorDocCitation] = Field(default_factory=list, description="Official vendor documentation citations")
