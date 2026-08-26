"""
Port Interface: Troubleshooting Audit Ledger Repository
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from backend.domain.entities.audit import AuditLedgerEntry


class IAuditRepository(ABC):
    """Abstract port for permanent troubleshooting audit ledger persistence."""

    @abstractmethod
    async def record_audit_entry(self, entry: AuditLedgerEntry) -> Optional[int]:
        """Persist a troubleshooting execution record."""
        pass

    @abstractmethod
    async def get_audit_history(
        self, limit: int = 20, vendor: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve recent audit ledger records."""
        pass

    @abstractmethod
    async def is_healthy(self) -> bool:
        """Check if audit repository storage is active."""
        pass
