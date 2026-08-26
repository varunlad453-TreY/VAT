"""
Application Layer DTO: Troubleshooting Requests & Responses
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.domain.entities.citation import VendorDocCitation
from backend.domain.entities.remediation import (
    PostCheckCommand,
    PreCheckCommand,
    RemediationCommand,
    RiskAssessment,
    RollbackCommand,
)


class TroubleshootRequestDTO(BaseModel):
    """Input payload DTO for troubleshooting synthesis."""
    incident_id: Optional[str] = Field(default=None, description="Optional incident ticket ID")
    device_id: Optional[str] = Field(default=None, description="Target device identifier/hostname")
    vendor: Optional[str] = Field(default=None, description="Target vendor platform")
    protocol: Optional[str] = Field(default=None, description="Optional target protocol")
    raw_logs: str = Field(..., description="Raw syslog stream or telemetry payload")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional telemetry context")


class ResolutionStepDTO(BaseModel):
    """Legacy backward-compatible resolution step DTO."""
    step_number: int
    action: str
    command: Optional[str] = None
    expected_output: Optional[str] = None
    explanation: str


class TroubleshootResponseDTO(BaseModel):
    """Output resolution playbook DTO."""
    incident_id: Optional[str] = None
    device_id: Optional[str] = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    vendor: str = "cisco"
    protocol: str = "general"
    diagnosis: str
    root_cause_hypothesis: str
    confidence_score: float
    model_used: str = "deterministic-rag-synthesizer"
    
    # 4-Stage Operational Runbook Lifecycle
    pre_checks: List[PreCheckCommand] = Field(default_factory=list)
    remediation_commands: List[RemediationCommand] = Field(default_factory=list)
    post_checks: List[PostCheckCommand] = Field(default_factory=list)
    rollback_playbook: List[RollbackCommand] = Field(default_factory=list)
    risk_assessment: RiskAssessment = Field(default_factory=RiskAssessment)
    
    # Backward compatibility & citations
    resolution_steps: List[ResolutionStepDTO] = Field(default_factory=list)
    cited_vendor_docs: List[VendorDocCitation] = Field(default_factory=list)
