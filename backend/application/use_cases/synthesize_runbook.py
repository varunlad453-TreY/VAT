"""
Application Use Case: Synthesize 4-Stage Remediation Runbook
Pure business logic orchestrating telemetry parsing, hybrid RAG retrieval, synthesis, and audit recording.
"""

import logging
from typing import List, Optional

from backend.application.dtos.troubleshoot_dto import (
    TroubleshootRequestDTO,
    TroubleshootResponseDTO,
)
from backend.application.ports.ai_synthesizer import IAISynthesizer
from backend.application.ports.audit_repository import IAuditRepository
from backend.application.ports.cache_service import ICacheService
from backend.application.ports.telemetry_parser import ITelemetryParser
from backend.application.ports.vector_repository import IVectorRepository
from backend.domain.entities.audit import AuditLedgerEntry
from backend.domain.entities.citation import VendorDocCitation

logger = logging.getLogger(__name__)


class SynthesizeRemediationRunbookUseCase:
    """Use case for end-to-end multi-vendor network troubleshooting and runbook generation."""

    def __init__(
        self,
        vector_repo: IVectorRepository,
        ai_synthesizer: IAISynthesizer,
        telemetry_parser: ITelemetryParser,
        audit_repo: Optional[IAuditRepository] = None,
        cache_service: Optional[ICacheService] = None,
    ) -> None:
        self._vector_repo = vector_repo
        self._ai_synthesizer = ai_synthesizer
        self._telemetry_parser = telemetry_parser
        self._audit_repo = audit_repo
        self._cache_service = cache_service

    async def execute(self, request: TroubleshootRequestDTO) -> TroubleshootResponseDTO:
        """
        Execute troubleshooting lifecycle:
        1. Tokenize/parse telemetry logs.
        2. Execute Hybrid Vector & Lexical search against vendor documentation.
        3. Synthesize deterministic 4-stage operational runbook.
        4. Persist audit ledger record.
        5. Publish real-time event notification.
        """
        # 1. Parse raw telemetry log
        parsed = self._telemetry_parser.parse_log(
            raw_log=request.raw_logs,
            device_hint=request.device_id,
        )

        effective_vendor = request.vendor or parsed.vendor
        effective_protocol = request.protocol or parsed.protocol
        effective_device = request.device_id or parsed.device_id

        # 2. Hybrid RRF Vector & Lexical Search
        relevant_docs = await self._vector_repo.find_relevant_docs(
            query_text=request.raw_logs,
            limit=3,
            vendor=effective_vendor,
            protocol=effective_protocol,
        )

        citations: List[VendorDocCitation] = [
            VendorDocCitation(
                source_url=doc["source_url"],
                title=doc["title"],
                vendor=doc.get("vendor", effective_vendor),
                similarity_score=round(float(doc.get("similarity", 0.88)), 3),
                excerpt=doc["chunk_text"][:280] + "...",
            )
            for doc in relevant_docs
        ]

        # 3. AI / Deterministic Runbook Synthesis
        response = await self._ai_synthesizer.synthesize_runbook(
            request=request,
            parsed_telemetry=parsed,
            citations=citations,
            relevant_docs=relevant_docs,
        )

        # 4. Permanent Audit Ledger Recording
        if self._audit_repo is not None:
            try:
                audit_entry = AuditLedgerEntry(
                    incident_id=response.incident_id or request.incident_id,
                    device_id=effective_device,
                    vendor=response.vendor,
                    raw_logs=request.raw_logs,
                    diagnosis=response.diagnosis,
                    root_cause=response.root_cause_hypothesis,
                    risk_level=response.risk_assessment.risk_level,
                    remediation_steps=[r.model_dump() for r in response.remediation_commands],
                    rollback_steps=[r.model_dump() for r in response.rollback_playbook],
                    cited_sources=[c.model_dump() for c in response.cited_vendor_docs],
                    confidence_score=response.confidence_score,
                    model_used=response.model_used,
                    executed_by="noc_operator",
                )
                await self._audit_repo.record_audit_entry(audit_entry)
            except Exception as exc:
                logger.warning("Audit ledger recording skipped: %s", exc)

        # 5. Real-Time Telemetry Event Publishing
        if self._cache_service is not None:
            try:
                await self._cache_service.publish(
                    channel="vat:telemetry:resolved",
                    message={
                        "incident_id": response.incident_id,
                        "device_id": effective_device,
                        "vendor": response.vendor,
                        "diagnosis": response.diagnosis,
                        "risk_level": response.risk_assessment.risk_level,
                    },
                )
            except Exception as exc:
                logger.debug("Cache pub/sub skipped: %s", exc)

        return response
