"""
Application Use Case: Ingest & Tokenize Telemetry Streams
Parses multi-vendor syslog batches and conditionally triggers auto-remediation synthesis.
"""

from typing import List, Optional

from backend.application.dtos.telemetry_dto import (
    TelemetryIngestBatchRequestDTO,
    TelemetryIngestResponseDTO,
)
from backend.application.dtos.troubleshoot_dto import (
    TroubleshootRequestDTO,
    TroubleshootResponseDTO,
)
from backend.application.ports.telemetry_parser import ITelemetryParser
from backend.application.use_cases.synthesize_runbook import SynthesizeRemediationRunbookUseCase
from backend.domain.entities.telemetry import ParsedTelemetry
from backend.domain.enums import SeverityLevel


class IngestTelemetryBatchUseCase:
    """Use case for batch ingestion of multi-vendor network telemetry."""

    def __init__(
        self,
        telemetry_parser: ITelemetryParser,
        synthesize_use_case: Optional[SynthesizeRemediationRunbookUseCase] = None,
    ) -> None:
        self._telemetry_parser = telemetry_parser
        self._synthesize_use_case = synthesize_use_case

    async def execute(self, request: TelemetryIngestBatchRequestDTO) -> TelemetryIngestResponseDTO:
        """
        Batch parse telemetry logs and optionally auto-generate remediation runbooks
        for high-severity incidents.
        """
        parsed_events: List[ParsedTelemetry] = []
        auto_runbooks: List[TroubleshootResponseDTO] = []

        for raw_log in request.logs:
            if not raw_log.strip():
                continue

            parsed = self._telemetry_parser.parse_log(
                raw_log=raw_log,
                device_hint=request.device_hint,
            )
            parsed_events.append(parsed)

            # Automatically trigger runbook synthesis for critical or error events if enabled
            if (
                request.auto_troubleshoot
                and self._synthesize_use_case is not None
                and parsed.severity in [SeverityLevel.CRITICAL.value, SeverityLevel.ERROR.value]
            ):
                troubleshoot_req = TroubleshootRequestDTO(
                    device_id=parsed.device_id,
                    vendor=parsed.vendor,
                    protocol=parsed.protocol,
                    raw_logs=raw_log,
                )
                runbook = await self._synthesize_use_case.execute(troubleshoot_req)
                auto_runbooks.append(runbook)

        return TelemetryIngestResponseDTO(
            total_received=len(parsed_events),
            parsed_events=parsed_events,
            troubleshooting_reports=auto_runbooks,
        )
