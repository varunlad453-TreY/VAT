"""
Presentation Layer Package (FastAPI Routers, Dependency Injection & WebSockets)
"""

from backend.presentation.api.health_router import router as health_router
from backend.presentation.api.telemetry_router import router as telemetry_router
from backend.presentation.api.troubleshoot_router import router as troubleshoot_router
from backend.presentation.dependencies import (
    get_ai_synthesizer,
    get_audit_repository,
    get_cache_service,
    get_ingest_telemetry_use_case,
    get_query_sources_use_case,
    get_synthesize_runbook_use_case,
    get_telemetry_parser,
    get_vector_repository,
)
from backend.presentation.websockets.telemetry_ws import (
    ConnectionManager,
    router as ws_router,
    ws_manager,
)

__all__ = [
    "troubleshoot_router",
    "telemetry_router",
    "health_router",
    "ws_router",
    "ws_manager",
    "ConnectionManager",
    "get_vector_repository",
    "get_ai_synthesizer",
    "get_telemetry_parser",
    "get_audit_repository",
    "get_cache_service",
    "get_synthesize_runbook_use_case",
    "get_ingest_telemetry_use_case",
    "get_query_sources_use_case",
]
