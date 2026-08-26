"""
Tests for Phase 3: Infrastructure Adapters & Application Layer Use Cases
Validates pgvector repository, in-memory air-gapped fallback, resilient AI synthesis,
audit ledger, Redis cache, and pure business logic use cases.
"""

import pytest

from backend.application.dtos.telemetry_dto import TelemetryIngestBatchRequestDTO
from backend.application.dtos.troubleshoot_dto import TroubleshootRequestDTO
from backend.application.use_cases.ingest_telemetry import IngestTelemetryBatchUseCase
from backend.application.use_cases.query_sources import QueryVendorSourcesUseCase
from backend.application.use_cases.synthesize_runbook import SynthesizeRemediationRunbookUseCase
from backend.domain.entities.audit import AuditLedgerEntry
from backend.domain.entities.citation import KnowledgeChunk
from backend.domain.enums import RiskLevel, SeverityLevel, VendorPlatform
from backend.infrastructure.ai.deterministic_synthesizer import DeterministicSynthesizer
from backend.infrastructure.ai.resilient_llm_adapter import ResilientLLMAdapter
from backend.infrastructure.cache.redis_service import RedisCacheService
from backend.infrastructure.parsing.regex_telemetry_parser import RegexTelemetryParser
from backend.infrastructure.repositories.in_memory_repository import (
    ENTERPRISE_FALLBACK_CORPUS,
    InMemoryVectorRepository,
)
from backend.infrastructure.repositories.pg_audit_repository import PgAuditRepository
from backend.infrastructure.repositories.pgvector_repository import AsyncpgVectorRepository


# ══════════════════════════════════════════════════════════════════════════════
# 1. In-Memory & pgvector Repository Tests (Hybrid RRF & Air-Gapped Fallback)
# ══════════════════════════════════════════════════════════════════════════════

class TestVectorRepositories:
    """Test suite for Vector repositories and air-gapped fallback mechanisms."""

    def test_in_memory_embedding_dimension_and_norm(self):
        repo = InMemoryVectorRepository()
        emb = repo.embed_text("OSPF neighbor stuck in EXSTART state MTU mismatch")
        assert len(emb) == 384
        # Verify L2 normalization (sum of squares ~ 1.0)
        norm = sum(x * x for x in emb)
        assert pytest.approx(norm, 0.01) == 1.0

    @pytest.mark.asyncio
    async def test_in_memory_hybrid_search_cisco_bgp(self):
        repo = InMemoryVectorRepository()
        results = await repo.find_relevant_docs(
            query_text="%BGP-5-ADJCHANGE: neighbor 10.10.10.1 Down - hold time expired",
            limit=2,
            vendor="cisco",
            protocol="bgp",
        )
        assert len(results) >= 1
        top = results[0]
        assert top["vendor"] == "cisco"
        assert "bgp" in top["title"].lower() or "bgp" in top["chunk_text"].lower()
        assert top["similarity"] > 0.70

    @pytest.mark.asyncio
    async def test_in_memory_hybrid_search_juniper_junos(self):
        repo = InMemoryVectorRepository()
        results = await repo.find_relevant_docs(
            query_text="rpd[1234]: RPD_BGP_NEIGHBOR_STATE_CHANGED: BGP peer 172.16.1.1 Idle HoldTimer",
            limit=2,
            vendor="juniper",
            protocol="bgp",
        )
        assert len(results) >= 1
        assert results[0]["vendor"] == "juniper"
        assert "junos" in results[0]["title"].lower()

    @pytest.mark.asyncio
    async def test_in_memory_hybrid_search_velocloud_pmtud(self):
        repo = InMemoryVectorRepository()
        results = await repo.find_relevant_docs(
            query_text="EDGE_LINK_DEGRADATION: WAN link GE3 packet loss 18.4% PMTUD_BLACKHOLE",
            limit=2,
            vendor="velocloud",
            protocol="ipsec",
        )
        assert len(results) >= 1
        assert results[0]["vendor"] == "velocloud"
        assert "velocloud" in results[0]["chunk_text"].lower()

    @pytest.mark.asyncio
    async def test_in_memory_hybrid_search_arista_mlag(self):
        repo = InMemoryVectorRepository()
        results = await repo.find_relevant_docs(
            query_text="%MLAG-4-SPLIT_BRAIN: MLAG peer link down; secondary nodes isolated",
            limit=2,
            vendor="arista",
            protocol="evpn",
        )
        assert len(results) >= 1
        assert results[0]["vendor"] == "arista"
        assert "mlag" in results[0]["chunk_text"].lower()

    @pytest.mark.asyncio
    async def test_in_memory_index_chunks(self):
        repo = InMemoryVectorRepository(corpus=[])
        new_chunk = KnowledgeChunk(
            source_url="https://cisco.com/doc/sample",
            title="Custom Sample TAC Guide",
            vendor="cisco",
            product_family="routing",
            protocol="bgp",
            error_codes=["%BGP-TEST"],
            chunk_text="Custom sample text for testing in-memory chunk insertion.",
        )
        count = await repo.index_chunks([new_chunk])
        assert count == 1
        res = await repo.find_relevant_docs("Custom sample text", limit=1)
        assert len(res) == 1
        assert res[0]["title"] == "Custom Sample TAC Guide"

    @pytest.mark.asyncio
    async def test_pgvector_repository_graceful_fallback(self):
        """When PostgreSQL is offline, AsyncpgVectorRepository seamlessly delegates to in-memory store."""
        repo = AsyncpgVectorRepository()
        results = await repo.find_relevant_docs(
            query_text="%OSPF-5-ADJCHG: EXSTART MTU mismatch",
            limit=2,
            vendor="cisco",
            protocol="ospf",
        )
        assert len(results) >= 1
        assert results[0]["vendor"] == "cisco"


# ══════════════════════════════════════════════════════════════════════════════
# 2. Audit Repository Tests (PostgreSQL & In-Memory Fallback)
# ══════════════════════════════════════════════════════════════════════════════

class TestAuditRepository:
    """Test suite for persistent audit ledger operations."""

    @pytest.mark.asyncio
    async def test_audit_record_and_retrieve_fallback(self):
        repo = PgAuditRepository()
        entry = AuditLedgerEntry(
            incident_id="INC-PHASE3-001",
            device_id="Border-Router-01",
            vendor="cisco",
            raw_logs="%BGP-5-ADJCHANGE: neighbor 10.10.10.1 Down",
            diagnosis="BGP Session Down",
            root_cause="Hold timer expired",
            risk_level=RiskLevel.MEDIUM.value,
            remediation_steps=[{"step": 1, "command": "neighbor 10.10.10.1 timers 30 90"}],
            rollback_steps=[{"step": 1, "command": "neighbor 10.10.10.1 timers 60 180"}],
            cited_sources=[{"title": "Cisco BGP Guide", "url": "https://cisco.com"}],
            confidence_score=0.97,
        )

        entry_id = await repo.record_audit_entry(entry)
        assert entry_id is not None

        history = await repo.get_audit_history(limit=5, vendor="cisco")
        assert len(history) >= 1
        assert history[0]["incident_id"] == "INC-PHASE3-001"
        assert history[0]["vendor"] == "cisco"


# ══════════════════════════════════════════════════════════════════════════════
# 3. Telemetry Parser Adapter Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestTelemetryParserAdapter:
    """Test suite for multi-vendor regex parser adapter."""

    def test_parse_cisco_bgp_log(self):
        parser = RegexTelemetryParser()
        log = "%BGP-5-ADJCHANGE: neighbor 192.168.10.2 Down - BGP Notification sent, hold time expired"
        parsed = parser.parse_log(log, device_hint="Cisco-Edge-01")
        assert parsed.vendor == VendorPlatform.CISCO.value
        assert parsed.event_code == "%BGP-5-ADJCHANGE"
        assert parsed.protocol == "bgp"
        assert parsed.peer_ip == "192.168.10.2"
        assert parsed.severity == SeverityLevel.CRITICAL.value

    def test_parse_juniper_junos_log(self):
        parser = RegexTelemetryParser()
        log = "rpd[4210]: RPD_BGP_NEIGHBOR_STATE_CHANGED: BGP peer 172.16.1.1 (External AS 65001) changed state from Established to Idle"
        parsed = parser.parse_log(log)
        assert parsed.vendor == VendorPlatform.JUNIPER.value
        assert parsed.event_code == "RPD_BGP_NEIGHBOR_STATE_CHANGED"
        assert parsed.protocol == "bgp"
        assert parsed.peer_ip == "172.16.1.1"

    def test_parse_velocloud_sdwan_log(self):
        parser = RegexTelemetryParser()
        log = "EDGE_LINK_DEGRADATION: WAN link GE3 packet loss 18.4% PMTUD_BLACKHOLE"
        parsed = parser.parse_log(log)
        assert parsed.vendor == VendorPlatform.VELOCLOUD.value
        assert parsed.event_code == "EDGE_LINK_DEGRADATION"
        assert parsed.interface == "GE3"
        assert parsed.category == "sdwan"

    def test_parse_arista_mlag_log(self):
        parser = RegexTelemetryParser()
        log = "%MLAG-4-SPLIT_BRAIN: MLAG peer link Port-Channel 10 down on Leaf-01"
        parsed = parser.parse_log(log)
        assert parsed.vendor == VendorPlatform.ARISTA.value
        assert parsed.event_code == "%MLAG-4-SPLIT_BRAIN"
        assert parsed.protocol == "evpn"
        assert parsed.interface == "Port-Channel 10"

    def test_batch_parse(self):
        parser = RegexTelemetryParser()
        logs = [
            "%OSPF-5-ADJCHG: Process 1, Nbr 192.168.1.2 on GigabitEthernet0/0/1 from EXSTART to DOWN",
            "%MLAG-4-SPLIT_BRAIN: MLAG peer link down",
        ]
        parsed_list = parser.batch_parse(logs)
        assert len(parsed_list) == 2
        assert parsed_list[0].vendor == VendorPlatform.CISCO.value
        assert parsed_list[1].vendor == VendorPlatform.ARISTA.value


# ══════════════════════════════════════════════════════════════════════════════
# 4. AI Synthesizer Adapter Tests (Deterministic & Resilient LLM Fallback)
# ══════════════════════════════════════════════════════════════════════════════

class TestAISynthesizers:
    """Test suite for AI Synthesizer adapters."""

    @pytest.mark.asyncio
    async def test_deterministic_synthesizer_cisco_bgp(self):
        synthesizer = DeterministicSynthesizer()
        parser = RegexTelemetryParser()
        req = TroubleshootRequestDTO(
            raw_logs="%BGP-5-ADJCHANGE: neighbor 10.10.10.1 Down - hold time expired",
            device_id="Core-RT-01",
        )
        parsed = parser.parse_log(req.raw_logs, device_hint=req.device_id)
        response = await synthesizer.synthesize_runbook(
            request=req,
            parsed_telemetry=parsed,
            citations=[],
            relevant_docs=[],
        )
        assert response.vendor == "cisco"
        assert response.protocol == "bgp"
        assert len(response.pre_checks) == 3
        assert len(response.remediation_commands) == 2
        assert len(response.post_checks) == 2
        assert len(response.rollback_playbook) == 1
        assert response.risk_assessment.risk_level == RiskLevel.MEDIUM.value
        assert response.remediation_commands[0].config_mode == "router bgp"

    @pytest.mark.asyncio
    async def test_deterministic_synthesizer_arista_mlag(self):
        synthesizer = DeterministicSynthesizer()
        parser = RegexTelemetryParser()
        req = TroubleshootRequestDTO(
            raw_logs="%MLAG-4-SPLIT_BRAIN: MLAG peer link down",
            device_id="Leaf-02",
        )
        parsed = parser.parse_log(req.raw_logs, device_hint=req.device_id)
        response = await synthesizer.synthesize_runbook(
            request=req,
            parsed_telemetry=parsed,
            citations=[],
            relevant_docs=[],
        )
        assert response.vendor == "arista"
        assert response.risk_assessment.risk_level == RiskLevel.HIGH.value
        assert "reload-delay mlag 300" in response.remediation_commands[0].command

    @pytest.mark.asyncio
    async def test_resilient_llm_adapter_fallback_when_no_key(self):
        adapter = ResilientLLMAdapter()
        parser = RegexTelemetryParser()
        req = TroubleshootRequestDTO(
            raw_logs="%OSPF-5-ADJCHG: EXSTART MTU mismatch",
            device_id="Edge-01",
        )
        parsed = parser.parse_log(req.raw_logs)
        response = await adapter.synthesize_runbook(
            request=req,
            parsed_telemetry=parsed,
            citations=[],
            relevant_docs=[],
        )
        assert response.vendor == "cisco"
        assert response.protocol == "ospf"
        assert len(response.pre_checks) > 0


# ══════════════════════════════════════════════════════════════════════════════
# 5. Redis Cache Service Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestRedisCacheService:
    """Test suite for Redis cache and event bus with in-memory fallback."""

    @pytest.mark.asyncio
    async def test_cache_set_and_get_fallback(self):
        cache = RedisCacheService()
        await cache.set("test_key", "test_val", ttl_seconds=60)
        val = await cache.get("test_key")
        assert val == "test_val"

    @pytest.mark.asyncio
    async def test_cache_publish_fallback(self):
        cache = RedisCacheService()
        received = []
        cache._in_memory_subscribers["test_channel"] = [lambda msg: received.append(msg)]
        published_count = await cache.publish("test_channel", {"event": "test"})
        assert published_count == 1
        assert len(received) == 1
        assert "test" in received[0]


# ══════════════════════════════════════════════════════════════════════════════
# 6. Application Layer Use Cases Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestApplicationUseCases:
    """Test suite for Pure Application Layer Use Cases."""

    @pytest.mark.asyncio
    async def test_synthesize_remediation_runbook_use_case(self):
        vector_repo = InMemoryVectorRepository()
        ai_synthesizer = DeterministicSynthesizer()
        telemetry_parser = RegexTelemetryParser()
        audit_repo = PgAuditRepository()
        cache_service = RedisCacheService()

        use_case = SynthesizeRemediationRunbookUseCase(
            vector_repo=vector_repo,
            ai_synthesizer=ai_synthesizer,
            telemetry_parser=telemetry_parser,
            audit_repo=audit_repo,
            cache_service=cache_service,
        )

        req = TroubleshootRequestDTO(
            raw_logs="rpd[1234]: RPD_BGP_NEIGHBOR_STATE_CHANGED: BGP peer 172.16.1.1 changed state from Established to Idle",
            device_id="Juniper-MX-01",
        )
        response = await use_case.execute(req)

        assert response.vendor == "juniper"
        assert response.protocol == "bgp"
        assert len(response.cited_vendor_docs) >= 1
        assert len(response.pre_checks) > 0
        assert len(response.remediation_commands) > 0
        assert len(response.post_checks) > 0
        assert len(response.rollback_playbook) > 0

        # Verify audit history received the entry
        history = await audit_repo.get_audit_history(limit=1, vendor="juniper")
        assert len(history) == 1
        assert history[0]["vendor"] == "juniper"

    @pytest.mark.asyncio
    async def test_ingest_telemetry_batch_use_case_with_auto_troubleshoot(self):
        parser = RegexTelemetryParser()
        vector_repo = InMemoryVectorRepository()
        ai_synthesizer = DeterministicSynthesizer()
        audit_repo = PgAuditRepository()

        synthesize_use_case = SynthesizeRemediationRunbookUseCase(
            vector_repo=vector_repo,
            ai_synthesizer=ai_synthesizer,
            telemetry_parser=parser,
            audit_repo=audit_repo,
        )

        ingest_use_case = IngestTelemetryBatchUseCase(
            telemetry_parser=parser,
            synthesize_use_case=synthesize_use_case,
        )

        batch_req = TelemetryIngestBatchRequestDTO(
            device_hint="Edge-Core-01",
            logs=[
                "%BGP-5-ADJCHANGE: neighbor 10.10.10.1 Down - hold time expired",
                "%SYS-5-CONFIG_I: Configured from console by admin",
            ],
            auto_troubleshoot=True,
        )

        res = await ingest_use_case.execute(batch_req)
        assert res.total_received == 2
        assert len(res.parsed_events) == 2
        # The critical BGP log should have auto-generated 1 runbook
        assert len(res.troubleshooting_reports) == 1
        assert res.troubleshooting_reports[0].vendor == "cisco"

    @pytest.mark.asyncio
    async def test_query_vendor_sources_use_case(self):
        vector_repo = InMemoryVectorRepository()
        use_case = QueryVendorSourcesUseCase(vector_repo=vector_repo)
        docs = await use_case.execute(vendor="cisco", protocol="ospf", limit=2)
        assert len(docs) >= 1
        assert docs[0]["vendor"] == "cisco"
