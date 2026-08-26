"""
Application Layer DTO: Telemetry Stream Ingestion
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from backend.application.dtos.troubleshoot_dto import TroubleshootResponseDTO
from backend.domain.entities.telemetry import ParsedTelemetry


class TelemetryIngestBatchRequestDTO(BaseModel):
    """Batch log ingestion request DTO."""
    logs: List[str] = Field(..., description="List of raw log messages or syslog lines")
    device_hint: Optional[str] = Field(default=None, description="Optional device hostname hint")
    auto_troubleshoot: bool = Field(default=False, description="Auto-trigger RAG troubleshooting on critical/error events")


class TelemetryIngestResponseDTO(BaseModel):
    """Batch log ingestion response DTO."""
    total_received: int
    parsed_events: List[ParsedTelemetry]
    troubleshooting_reports: List[TroubleshootResponseDTO] = Field(default_factory=list)
