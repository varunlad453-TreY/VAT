"""
Presentation Layer: Troubleshooting API Router
Thin HTTP controller delegating to application use cases via Dependency Injection.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.application.dtos.troubleshoot_dto import (
    TroubleshootRequestDTO,
    TroubleshootResponseDTO,
)
from backend.application.ports.audit_repository import IAuditRepository
from backend.application.use_cases.query_sources import QueryVendorSourcesUseCase
from backend.application.use_cases.synthesize_runbook import SynthesizeRemediationRunbookUseCase
from backend.domain.entities.citation import VendorDocCitation
from backend.presentation.dependencies import (
    get_audit_repository,
    get_query_sources_use_case,
    get_synthesize_runbook_use_case,
)

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
    response_model=TroubleshootResponseDTO,
    summary="Generate Enterprise Multi-Vendor AI Troubleshooting Runbook",
    description=(
        "Analyzes multi-vendor error telemetry (Cisco, Juniper, VeloCloud, Arista), executes "
        "hybrid vector search via pgvector and full-text GIN index, and generates a full 4-stage "
        "remediation playbook (Pre-Checks -> Exact CLI Fixes -> Post-Checks -> Rollback) with blast radius assessment."
    ),
)
async def troubleshoot_error_log(
    request: TroubleshootRequestDTO,
    use_case: SynthesizeRemediationRunbookUseCase = Depends(get_synthesize_runbook_use_case),
) -> TroubleshootResponseDTO:
    """Analyze error log and generate grounded 4-stage remediation runbook."""
    if not request.raw_logs or not request.raw_logs.strip():
        raise HTTPException(
            status_code=422,
            detail="raw_logs field cannot be empty",
        )

    try:
        response = await use_case.execute(request)
        return response
    except Exception as exc:
        logger.error("Error during troubleshooting use case execution: %s", exc, exc_info=True)
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
    use_case: QueryVendorSourcesUseCase = Depends(get_query_sources_use_case),
) -> List[VendorDocCitation]:
    """Retrieve indexed vendor manual citations via hybrid vector search."""
    try:
        docs = await use_case.execute(vendor=vendor, protocol=protocol, limit=limit)
        return [
            VendorDocCitation(
                source_url=d["source_url"],
                title=d["title"],
                vendor=d.get("vendor", "cisco"),
                similarity_score=round(float(d.get("similarity", 0.88)), 3),
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
    audit_repo: IAuditRepository = Depends(get_audit_repository),
) -> List[Dict[str, Any]]:
    """Retrieve audit history from audit repository."""
    try:
        return await audit_repo.get_audit_history(limit=limit, vendor=vendor)
    except Exception as exc:
        logger.error("Audit ledger query failed: %s", exc)
        return []
