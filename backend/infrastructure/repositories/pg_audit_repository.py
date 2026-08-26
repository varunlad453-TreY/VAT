"""
Infrastructure Adapter: PostgreSQL Audit Ledger Repository
Permanent audit tracking for troubleshooting and remediation operations.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from backend.application.ports.audit_repository import IAuditRepository
from backend.database.client import db
from backend.domain.entities.audit import AuditLedgerEntry

logger = logging.getLogger(__name__)


class PgAuditRepository(IAuditRepository):
    """PostgreSQL Audit Ledger Repository with in-memory fallback buffer."""

    def __init__(self) -> None:
        self._in_memory_log: List[Dict[str, Any]] = []

    async def record_audit_entry(self, entry: AuditLedgerEntry) -> Optional[int]:
        """Persist a troubleshooting session record to PostgreSQL or fallback buffer."""
        remediation_json = json.dumps(entry.remediation_steps)
        rollback_json = json.dumps(entry.rollback_steps)
        citations_json = json.dumps(entry.cited_sources)

        try:
            if await db.is_connected():
                query = """
                    INSERT INTO troubleshooting_audit_ledger (
                        incident_id, device_id, vendor, raw_logs, diagnosis, root_cause,
                        risk_level, remediation_steps, rollback_steps, cited_sources,
                        confidence_score, model_used, executed_by, created_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb, $10::jsonb, $11, $12, $13, $14
                    )
                    RETURNING id;
                """
                row_id = await db.fetchval(
                    query,
                    entry.incident_id,
                    entry.device_id,
                    entry.vendor,
                    entry.raw_logs,
                    entry.diagnosis,
                    entry.root_cause,
                    entry.risk_level,
                    remediation_json,
                    rollback_json,
                    citations_json,
                    entry.confidence_score,
                    entry.model_used,
                    entry.executed_by,
                    entry.created_at,
                )
                return int(row_id) if row_id is not None else None
        except Exception as exc:
            logger.debug("Database audit record insertion error, falling back to memory buffer: %s", exc)

        # In-memory buffer fallback
        mem_id = len(self._in_memory_log) + 1
        record = {
            "id": mem_id,
            "incident_id": entry.incident_id,
            "device_id": entry.device_id,
            "vendor": entry.vendor,
            "raw_logs": entry.raw_logs,
            "diagnosis": entry.diagnosis,
            "root_cause": entry.root_cause,
            "risk_level": entry.risk_level,
            "remediation_steps": entry.remediation_steps,
            "rollback_steps": entry.rollback_steps,
            "cited_sources": entry.cited_sources,
            "confidence_score": entry.confidence_score,
            "model_used": entry.model_used,
            "executed_by": entry.executed_by,
            "created_at": entry.created_at.isoformat(),
        }
        self._in_memory_log.insert(0, record)
        if len(self._in_memory_log) > 200:
            self._in_memory_log.pop()
        return mem_id

    async def get_audit_history(
        self, limit: int = 20, vendor: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve recent audit ledger entries."""
        v_filter = vendor.lower() if vendor and vendor.lower() not in ["generic", "all"] else None

        try:
            if await db.is_connected():
                query = """
                    SELECT 
                        id, incident_id, device_id, vendor, raw_logs, diagnosis, root_cause,
                        risk_level, remediation_steps, rollback_steps, cited_sources,
                        confidence_score, model_used, executed_by, created_at
                    FROM troubleshooting_audit_ledger
                    WHERE ($1::text IS NULL OR vendor = $1)
                    ORDER BY created_at DESC
                    LIMIT $2;
                """
                rows = await db.fetch(query, v_filter, limit)
                if rows:
                    results = []
                    for r in rows:
                        results.append({
                            "id": r["id"],
                            "incident_id": r["incident_id"],
                            "device_id": r["device_id"],
                            "vendor": r["vendor"],
                            "raw_logs": r["raw_logs"],
                            "diagnosis": r["diagnosis"],
                            "root_cause": r["root_cause"],
                            "risk_level": r["risk_level"],
                            "remediation_steps": json.loads(r["remediation_steps"]) if isinstance(r["remediation_steps"], str) else r["remediation_steps"],
                            "rollback_steps": json.loads(r["rollback_steps"]) if isinstance(r["rollback_steps"], str) else r["rollback_steps"],
                            "cited_sources": json.loads(r["cited_sources"]) if isinstance(r["cited_sources"], str) else r["cited_sources"],
                            "confidence_score": float(r["confidence_score"]),
                            "model_used": r["model_used"],
                            "executed_by": r["executed_by"],
                            "created_at": r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else str(r["created_at"]),
                        })
                    return results
        except Exception as exc:
            logger.debug("Database audit history query error, using memory buffer: %s", exc)

        # Filter in-memory buffer
        if v_filter:
            filtered = [r for r in self._in_memory_log if r.get("vendor") == v_filter]
            return filtered[:limit]
        return self._in_memory_log[:limit]

    async def is_healthy(self) -> bool:
        """Check if audit persistence is active."""
        try:
            return await db.is_connected()
        except Exception:
            return False
