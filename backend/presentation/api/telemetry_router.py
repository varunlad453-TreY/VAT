"""
Presentation Layer: Telemetry Ingestion & Parsing API Router
Thin HTTP controller delegating to telemetry use cases and parser ports.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.application.dtos.telemetry_dto import (
    TelemetryIngestBatchRequestDTO,
    TelemetryIngestResponseDTO,
)
from backend.application.ports.telemetry_parser import ITelemetryParser
from backend.application.use_cases.ingest_telemetry import IngestTelemetryBatchUseCase
from backend.domain.entities.telemetry import ParsedTelemetry
from backend.presentation.dependencies import (
    get_ingest_telemetry_use_case,
    get_telemetry_parser,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/telemetry",
    tags=["telemetry"],
    responses={
        500: {"description": "Telemetry processing failure"},
    },
)


@router.post(
    "/parse",
    response_model=ParsedTelemetry,
    summary="Parse Single Raw Telemetry Line",
    description="Extracts normalized vendor, protocol, interface, event code, and severity from raw log message.",
)
async def parse_single_log(
    raw_log: str = Query(..., description="Raw syslog line to parse"),
    device_hint: Optional[str] = Query(None, description="Optional device hostname hint"),
    parser: ITelemetryParser = Depends(get_telemetry_parser),
) -> ParsedTelemetry:
    """Parse raw log and return normalized event."""
    return parser.parse_log(raw_log, device_hint=device_hint)


@router.post(
    "/ingest",
    response_model=TelemetryIngestResponseDTO,
    summary="Ingest Telemetry Stream Batch",
    description="Ingests syslog stream batch, parses all entries, and optionally executes immediate automated RAG troubleshooting.",
)
async def ingest_telemetry_stream(
    request: TelemetryIngestBatchRequestDTO,
    use_case: IngestTelemetryBatchUseCase = Depends(get_ingest_telemetry_use_case),
) -> TelemetryIngestResponseDTO:
    """Ingest and process log batch."""
    if not request.logs:
        raise HTTPException(status_code=422, detail="No log entries provided")

    return await use_case.execute(request)
