"""
Domain Entity: Troubleshooting Audit Ledger Record
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


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
