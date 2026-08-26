"""
Vendor-Aware Troubleshooting API Routes (VAT Phase 2)
"""

import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.database.client import db
from backend.models.troubleshoot import (
    TroubleshootRequest,
    TroubleshootResponse,
    VendorDocCitation,
)
from backend.services.ai_service import ai_service
from backend.services.vector_service import vector_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/troubleshoot",
    tags=["troubleshoot"],
    responses={
        500: {"description": "Internal server error during diagnostic synthesis"},
    },
)


@router.post(
    "",
    response_model=TroubleshootResponse,
    summary="Generate Enterprise Multi-Vendor AI Troubleshooting Playbook",
    description=(
        "Analyzes multi-vendor error telemetry (Cisco, Juniper, VeloCloud, Arista), executes "
        "hybrid vector search via pgvector and full-text GIN index, and generates a full 3-stage "
        "remediation playbook (Pre-Checks -> Exact CLI Fixes -> Post-Checks -> Rollback) with blast radius assessment."
    ),
)
async def troubleshoot_error_log(request: TroubleshootRequest) -> TroubleshootResponse:
    """Analyze error log and generate cited remediation playbook."""
    if not request.raw_logs or not request.raw_logs.strip():
        raise HTTPException(
            status_code=422,
            detail="raw_logs field cannot be empty",
        )

    try:
        response = await ai_service.suggest_resolution_from_docs(request)
        return response
    except Exception as exc:
        logger.error("Error generating troubleshooting resolution: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Troubleshooting analysis failed: {str(exc)}",
        )


@router.get(
    "/sources",
    response_model=List[VendorDocCitation],
    summary="Query Multi-Vendor Knowledge Base",
    description="Returns vendor documentation sources matching query, vendor, and protocol filters.",
)
async def list_vendor_sources(
    query: str = Query("BGP neighbor reset hold time expired", description="Search query"),
    vendor: Optional[str] = Query(None, description="Optional vendor filter ('cisco', 'juniper', 'velocloud', 'arista')"),
    protocol: Optional[str] = Query(None, description="Optional protocol filter ('bgp', 'ospf', 'ipsec', 'evpn')"),
    limit: int = Query(5, ge=1, le=20, description="Max documentation chunks to return"),
) -> List[VendorDocCitation]:
    """Retrieve indexed vendor manual citations via hybrid vector search."""
    try:
        docs = await vector_service.find_relevant_docs(
            query_text=query, limit=limit, vendor=vendor, protocol=protocol
        )
        return [
            VendorDocCitation(
                source_url=d["source_url"],
                title=d["title"],
                vendor=d.get("vendor", "cisco"),
                similarity_score=round(d.get("similarity", 0.88), 3),
                excerpt=d["chunk_text"][:280] + "...",
            )
            for d in docs
        ]
    except Exception as exc:
        logger.error("Error querying vendor sources: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vendor sources query failed: {str(exc)}",
        )


@router.get(
    "/audit",
    summary="Get Troubleshooting Audit Ledger History",
    description="Fetches recent permanent troubleshooting and remediation audit logs.",
)
async def get_troubleshooting_audit_history(
    limit: int = Query(20, ge=1, le=100),
    vendor: Optional[str] = Query(None),
) -> List[Dict[str, Any]]:
    """Retrieve audit history from PostgreSQL."""
    try:
        if await db.is_connected():
            query = """
                SELECT id, incident_id, device_id, vendor, raw_logs, diagnosis, root_cause,
                       risk_level, remediation_steps, rollback_steps, cited_sources,
                       confidence_score, model_used, created_at
                FROM troubleshooting_audit_ledger
                WHERE ($1::text IS NULL OR vendor = $1)
                ORDER BY created_at DESC
                LIMIT $2;
            """
            rows = await db.fetch(query, vendor, limit)
            result = []
            for r in rows:
                row_dict = dict(r)
                if isinstance(row_dict.get("remediation_steps"), str):
                    row_dict["remediation_steps"] = json.loads(row_dict["remediation_steps"])
                if isinstance(row_dict.get("rollback_steps"), str):
                    row_dict["rollback_steps"] = json.loads(row_dict["rollback_steps"])
                if isinstance(row_dict.get("cited_sources"), str):
                    row_dict["cited_sources"] = json.loads(row_dict["cited_sources"])
                result.append(row_dict)
            return result
    except Exception as exc:
        logger.debug("Audit ledger query failed: %s", exc)

    return []
