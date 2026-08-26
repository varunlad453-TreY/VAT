"""
Domain Entity: Telemetry & Event Models
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from backend.domain.enums import SeverityLevel, VendorPlatform, ProtocolType


class ParsedTelemetry(BaseModel):
    """Normalized multi-vendor telemetry domain entity."""
    raw_log: str = Field(..., description="Raw unprocessed syslog or error payload")
    vendor: str = Field(default=VendorPlatform.GENERIC.value, description="Detected vendor platform")
    device_id: str = Field(default="Core-Router-01", description="Extracted device identifier")
    event_code: Optional[str] = Field(default=None, description="Standardized vendor event code")
    protocol: Optional[str] = Field(default=ProtocolType.GENERAL.value, description="Inferred protocol")
    interface: Optional[str] = Field(default=None, description="Extracted interface name")
    peer_ip: Optional[str] = Field(default=None, description="Extracted peer or neighbor IP")
    severity: str = Field(default=SeverityLevel.WARNING.value, description="Normalized severity grade")
    category: str = Field(default="routing", description="Event domain category")
    extracted_keywords: List[str] = Field(default_factory=list, description="Extracted tokens for hybrid search")


class TelemetryEvent(BaseModel):
    """Event wrapper for streaming ingestion."""
    event_id: str = Field(..., description="Unique event identifier")
    timestamp_epoch: float = Field(..., description="Timestamp in seconds since epoch")
    telemetry: ParsedTelemetry
