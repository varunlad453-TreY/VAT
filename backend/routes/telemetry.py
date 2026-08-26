"""
Telemetry Stream Ingestion & Parsing API Routes
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.models.troubleshoot import TroubleshootRequest, TroubleshootResponse
from backend.services.ai_service import ai_service
from backend.services.telemetry_parser import ParsedTelemetry, telemetry_parser

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/telemetry",
    tags=["telemetry"],
    responses={
        500: {"description": "Telemetry processing failure"},
    },
)


class TelemetryIngestBatchRequest(BaseModel):
    """Batch or single log ingestion request."""
    logs: List[str] = Field(..., description="List of raw log messages or syslog lines")
    device_hint: Optional[str] = Field(default=None, description="Optional device hostname hint")
    auto_troubleshoot: bool = Field(default=False, description="Automatically trigger RAG troubleshooting on critical/error events")


class TelemetryIngestResponse(BaseModel):
    """Response returned from telemetry ingestion."""
    total_received: int
    parsed_events: List[ParsedTelemetry]
    troubleshooting_reports: List[TroubleshootResponse] = Field(default_factory=list)


@router.post(
    "/parse",
    response_model=ParsedTelemetry,
    summary="Parse Single Raw Telemetry Line",
    description="Extracts normalized vendor, protocol, interface, event code, and severity from raw log message.",
)
async def parse_single_log(
    raw_log: str = Query(..., description="Raw syslog line to parse"),
    device_hint: Optional[str] = Query(None, description="Optional device hostname hint"),
) -> ParsedTelemetry:
    """Parse raw log and return normalized event."""
    return telemetry_parser.parse_log(raw_log, device_hint=device_hint)


@router.post(
    "/ingest",
    response_model=TelemetryIngestResponse,
    summary="Ingest Telemetry Stream Batch",
    description="Ingests syslog stream batch, parses all entries, and optionally executes immediate automated RAG troubleshooting.",
)
async def ingest_telemetry_stream(
    request: TelemetryIngestBatchRequest,
) -> TelemetryIngestResponse:
    """Ingest and process log batch."""
    if not request.logs:
        raise HTTPException(status_code=422, detail="No log entries provided")

    parsed_list: List[ParsedTelemetry] = []
    reports: List[TroubleshootResponse] = []

    for log_line in request.logs:
        if not log_line.strip():
            continue
        parsed = telemetry_parser.parse_log(log_line, device_hint=request.device_hint)
        parsed_list.append(parsed)

        # Trigger auto-troubleshoot if requested and event is actionable (CRITICAL/ERROR)
        if request.auto_troubleshoot and parsed.severity in ["CRITICAL", "ERROR"]:
            try:
                diag_req = TroubleshootRequest(
                    device_id=parsed.device_id,
                    vendor=parsed.vendor,
                    raw_logs=parsed.raw_log,
                )
                diag_resp = await ai_service.suggest_resolution_from_docs(diag_req)
                reports.append(diag_resp)
            except Exception as exc:
                logger.warning("Auto-troubleshooting failed for event: %s", exc)

    return TelemetryIngestResponse(
        total_received=len(parsed_list),
        parsed_events=parsed_list,
        troubleshooting_reports=reports,
    )
