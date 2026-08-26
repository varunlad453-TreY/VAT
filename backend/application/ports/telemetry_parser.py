"""
Port Interface: Telemetry Stream Parser & Tokenizer
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from backend.domain.entities.telemetry import ParsedTelemetry


class ITelemetryParser(ABC):
    """Abstract port for multi-vendor syslog and telemetry parsing."""

    @abstractmethod
    def parse_log(self, raw_log: str, device_hint: Optional[str] = None) -> ParsedTelemetry:
        """Parse raw log and return normalized telemetry domain entity."""
        pass

    @abstractmethod
    def batch_parse(self, logs: List[str], device_hint: Optional[str] = None) -> List[ParsedTelemetry]:
        """Batch parse multiple raw logs."""
        pass
