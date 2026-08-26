"""
Port Interface: AI Remediation Runbook Synthesizer
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from backend.application.dtos.troubleshoot_dto import (
    TroubleshootRequestDTO,
    TroubleshootResponseDTO,
)
from backend.domain.entities.citation import VendorDocCitation
from backend.domain.entities.telemetry import ParsedTelemetry


class IAISynthesizer(ABC):
    """Abstract port for RAG-grounded 4-stage remediation runbook synthesis."""

    @abstractmethod
    async def synthesize_runbook(
        self,
        request: TroubleshootRequestDTO,
        parsed_telemetry: ParsedTelemetry,
        citations: List[VendorDocCitation],
        relevant_docs: List[Dict[str, Any]],
    ) -> TroubleshootResponseDTO:
        """Synthesize a complete 4-stage remediation runbook from grounded vendor docs."""
        pass
