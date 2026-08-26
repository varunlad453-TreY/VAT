"""
Presentation Layer: Health & System Probes API Router
"""

from datetime import datetime, timezone
from typing import Dict
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.application.ports.audit_repository import IAuditRepository
from backend.application.ports.cache_service import ICacheService
from backend.application.ports.vector_repository import IVectorRepository
from backend.database.client import db
from backend.presentation.dependencies import (
    get_audit_repository,
    get_cache_service,
    get_vector_repository,
)

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    database_connected: bool
    version: str
    timestamp: datetime


@router.get("/health", response_model=HealthResponse)
async def health_check(
    vector_repo: IVectorRepository = Depends(get_vector_repository),
    audit_repo: IAuditRepository = Depends(get_audit_repository),
    cache_service: ICacheService = Depends(get_cache_service),
) -> HealthResponse:
    """Service health and database connectivity probe."""
    db_ok = await db.is_connected()
    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        service="vendor-aware-troubleshooter-enterprise",
        database_connected=db_ok,
        version="2.0.0",
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/")
async def root() -> Dict[str, str]:
    """Root metadata endpoint."""
    return {
        "service": "Vendor-Aware AI Troubleshooter (VAT Enterprise)",
        "version": "2.0.0",
        "docs_url": "/docs",
        "health_url": "/health",
        "console_url": "/console",
        "troubleshoot_url": "/troubleshoot",
        "telemetry_url": "/telemetry/ingest",
        "ws_telemetry_url": "/ws/telemetry",
        "ws_troubleshoot_url": "/ws/troubleshoot",
    }
