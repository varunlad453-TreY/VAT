"""
Presentation Layer: Dependency Injection Container
Wires concrete infrastructure adapters to application port interfaces and use cases.
"""

from typing import Optional
from fastapi import Depends

from backend.application.ports.ai_synthesizer import IAISynthesizer
from backend.application.ports.audit_repository import IAuditRepository
from backend.application.ports.cache_service import ICacheService
from backend.application.ports.telemetry_parser import ITelemetryParser
from backend.application.ports.vector_repository import IVectorRepository
from backend.application.use_cases.ingest_telemetry import IngestTelemetryBatchUseCase
from backend.application.use_cases.query_sources import QueryVendorSourcesUseCase
from backend.application.use_cases.synthesize_runbook import SynthesizeRemediationRunbookUseCase
from backend.infrastructure.ai.deterministic_synthesizer import DeterministicSynthesizer
from backend.infrastructure.ai.resilient_llm_adapter import ResilientLLMAdapter
from backend.infrastructure.cache.redis_service import RedisCacheService
from backend.infrastructure.parsing.regex_telemetry_parser import RegexTelemetryParser
from backend.infrastructure.repositories.in_memory_repository import InMemoryVectorRepository
from backend.infrastructure.repositories.pg_audit_repository import PgAuditRepository
from backend.infrastructure.repositories.pgvector_repository import AsyncpgVectorRepository

# Singleton infrastructure adapter instances
_fallback_vector_repo = InMemoryVectorRepository()
_pgvector_repo = AsyncpgVectorRepository(fallback_repo=_fallback_vector_repo)
_audit_repo = PgAuditRepository()
_deterministic_synthesizer = DeterministicSynthesizer()
_resilient_llm_adapter = ResilientLLMAdapter(fallback_synthesizer=_deterministic_synthesizer)
_telemetry_parser = RegexTelemetryParser()
_cache_service = RedisCacheService()


def get_vector_repository() -> IVectorRepository:
    """Dependency provider for Hybrid Vector & Lexical Repository."""
    return _pgvector_repo


def get_in_memory_vector_repository() -> IVectorRepository:
    """Dependency provider for Air-Gapped Fallback Vector Repository."""
    return _fallback_vector_repo


def get_ai_synthesizer() -> IAISynthesizer:
    """Dependency provider for Resilient AI Runbook Synthesizer."""
    return _resilient_llm_adapter


def get_deterministic_synthesizer() -> IAISynthesizer:
    """Dependency provider for Deterministic AI Synthesizer."""
    return _deterministic_synthesizer


def get_telemetry_parser() -> ITelemetryParser:
    """Dependency provider for Multi-Vendor Regex Telemetry Parser."""
    return _telemetry_parser


def get_audit_repository() -> IAuditRepository:
    """Dependency provider for Permanent Audit Ledger Repository."""
    return _audit_repo


def get_cache_service() -> ICacheService:
    """Dependency provider for Redis Cache & Event Bus Service."""
    return _cache_service


def get_synthesize_runbook_use_case(
    vector_repo: IVectorRepository = Depends(get_vector_repository),
    ai_synthesizer: IAISynthesizer = Depends(get_ai_synthesizer),
    telemetry_parser: ITelemetryParser = Depends(get_telemetry_parser),
    audit_repo: IAuditRepository = Depends(get_audit_repository),
    cache_service: ICacheService = Depends(get_cache_service),
) -> SynthesizeRemediationRunbookUseCase:
    """Dependency provider for SynthesizeRemediationRunbookUseCase."""
    return SynthesizeRemediationRunbookUseCase(
        vector_repo=vector_repo,
        ai_synthesizer=ai_synthesizer,
        telemetry_parser=telemetry_parser,
        audit_repo=audit_repo,
        cache_service=cache_service,
    )


def get_ingest_telemetry_use_case(
    telemetry_parser: ITelemetryParser = Depends(get_telemetry_parser),
    synthesize_use_case: SynthesizeRemediationRunbookUseCase = Depends(get_synthesize_runbook_use_case),
) -> IngestTelemetryBatchUseCase:
    """Dependency provider for IngestTelemetryBatchUseCase."""
    return IngestTelemetryBatchUseCase(
        telemetry_parser=telemetry_parser,
        synthesize_use_case=synthesize_use_case,
    )


def get_query_sources_use_case(
    vector_repo: IVectorRepository = Depends(get_vector_repository),
) -> QueryVendorSourcesUseCase:
    """Dependency provider for QueryVendorSourcesUseCase."""
    return QueryVendorSourcesUseCase(vector_repo=vector_repo)
