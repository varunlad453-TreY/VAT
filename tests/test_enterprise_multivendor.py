"""
Enterprise Multi-Vendor Integration Test Suite (VAT Phase 2)

Verifies multi-vendor parsing, hybrid search, 3-stage remediation generation,
blast radius risk scoring, telemetry ingestion stream, and audit logging.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.troubleshoot import TroubleshootRequest, TroubleshootResponse
from backend.services.ai_service import ai_service
from backend.services.telemetry_parser import telemetry_parser
from backend.services.vector_service import vector_service


@pytest.fixture
def client():
    return TestClient(app)


class TestTelemetryParserService:
    """Test multi-vendor telemetry parsing and regex token extraction."""

    def test_cisco_bgp_parser(self):
        log = "%BGP-5-ADJCHANGE: neighbor 10.10.10.1 Down - BGP Notification sent, hold time expired"
        parsed = telemetry_parser.parse_log(log, device_hint="Edge-Router-01")
        assert parsed.vendor == "cisco"
        assert parsed.protocol == "bgp"
        assert parsed.peer_ip == "10.10.10.1"
        assert parsed.event_code == "%BGP-5-ADJCHANGE"
        assert parsed.severity == "CRITICAL"

    def test_juniper_bgp_parser(self):
        log = "rpd[1234]: RPD_BGP_NEIGHBOR_STATE_CHANGED: BGP peer 172.16.1.1 (External AS 65001) changed state from Established to Idle"
        parsed = telemetry_parser.parse_log(log, device_hint="MX960-PE-01")
        assert parsed.vendor == "juniper"
        assert parsed.protocol == "bgp"
        assert parsed.peer_ip == "172.16.1.1"
        assert "RPD_BGP_NEIGHBOR_STATE_CHANGED" in parsed.event_code

    def test_velocloud_sdwan_parser(self):
        log = "EDGE_LINK_DEGRADATION: WAN link GE3 packet loss 18.4% exceeding SLA threshold"
        parsed = telemetry_parser.parse_log(log, device_hint="Branch-540")
        assert parsed.vendor == "velocloud"
        assert parsed.category == "sdwan"
        assert parsed.protocol == "ipsec"
        assert parsed.interface == "GE3"
        assert parsed.severity == "ERROR"

    def test_arista_mlag_parser(self):
        log = "%MLAG-4-SPLIT_BRAIN: MLAG peer link down; secondary nodes isolated"
        parsed = telemetry_parser.parse_log(log, device_hint="Leaf-Pair-01")
        assert parsed.vendor == "arista"
        assert parsed.protocol == "evpn"
        assert parsed.event_code == "%MLAG-4-SPLIT_BRAIN"
        assert parsed.severity == "CRITICAL"


class TestMultiVendorHybridSearch:
    """Test hybrid vector search filtering across vendor knowledge bases."""

    @pytest.mark.asyncio
    async def test_hybrid_search_cisco_bgp(self):
        query = "%BGP-5-ADJCHANGE neighbor 10.10.10.1 hold time expired"
        docs = await vector_service.find_relevant_docs(query, limit=2, vendor="cisco", protocol="bgp")
        assert len(docs) > 0
        assert docs[0]["vendor"] == "cisco"
        assert "13753" in docs[0]["source_url"] or "bgp" in docs[0]["chunk_text"].lower()

    @pytest.mark.asyncio
    async def test_hybrid_search_juniper_junos(self):
        query = "RPD_BGP_NEIGHBOR_STATE_CHANGED hold-time timeout"
        docs = await vector_service.find_relevant_docs(query, limit=2, vendor="juniper", protocol="bgp")
        assert len(docs) > 0
        assert docs[0]["vendor"] == "juniper"

    @pytest.mark.asyncio
    async def test_hybrid_search_velocloud_pmtud(self):
        query = "VeloCloud VCMP overlay MTU blackhole packet loss"
        docs = await vector_service.find_relevant_docs(query, limit=2, vendor="velocloud")
        assert len(docs) > 0
        assert docs[0]["vendor"] == "velocloud"

    @pytest.mark.asyncio
    async def test_hybrid_search_arista_mlag(self):
        query = "%MLAG-4-SPLIT_BRAIN peer link down"
        docs = await vector_service.find_relevant_docs(query, limit=2, vendor="arista")
        assert len(docs) > 0
        assert docs[0]["vendor"] == "arista"


class TestEnterpriseRemediationLifecycle:
    """Test 3-stage remediation, risk scoring, and rollback playbooks."""

    @pytest.mark.asyncio
    async def test_cisco_bgp_remediation_generation(self):
        req = TroubleshootRequest(
            device_id="Edge-Core-01",
            vendor="cisco",
            raw_logs="%BGP-5-ADJCHANGE: neighbor 10.10.10.1 Down - BGP Notification sent, hold time expired",
        )
        resp = await ai_service.suggest_resolution_from_docs(req)
        assert isinstance(resp, TroubleshootResponse)
        assert "BGP" in resp.diagnosis.upper()
        assert resp.risk_assessment.risk_level in ["LOW", "MEDIUM", "HIGH"]
        assert len(resp.pre_checks) > 0
        assert len(resp.remediation_commands) > 0
        assert len(resp.post_checks) > 0
        assert len(resp.rollback_playbook) > 0
        assert any("neighbor 10.10.10.1" in r.command for r in resp.remediation_commands)

    @pytest.mark.asyncio
    async def test_arista_mlag_split_brain_high_risk(self):
        req = TroubleshootRequest(
            device_id="Leaf-Switch-01",
            vendor="arista",
            raw_logs="%MLAG-4-SPLIT_BRAIN: MLAG peer link down; secondary nodes isolated",
        )
        resp = await ai_service.suggest_resolution_from_docs(req)
        assert resp.vendor == "arista"
        assert resp.risk_assessment.risk_level == "HIGH"
        assert any("reload-delay" in r.command or "port-channel" in r.command for r in resp.remediation_commands)


class TestEnterpriseTelemetryAPI:
    """Test Telemetry Stream Ingestion & Parsing Endpoints."""

    def test_parse_endpoint(self, client):
        res = client.post("/telemetry/parse?raw_log=%25BGP-5-ADJCHANGE:+neighbor+192.168.1.1+Down")
        assert res.status_code == 200
        data = res.json()
        assert data["vendor"] == "cisco"
        assert data["protocol"] == "bgp"

    def test_batch_ingest_with_auto_troubleshoot(self, client):
        payload = {
            "logs": [
                "%BGP-5-ADJCHANGE: neighbor 10.10.10.1 Down - BGP Notification sent, hold time expired",
                "rpd[1234]: RPD_BGP_NEIGHBOR_STATE_CHANGED: BGP peer 172.16.1.1 changed state from Established to Idle",
            ],
            "auto_troubleshoot": True,
        }
        res = client.post("/telemetry/ingest", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["total_received"] == 2
        assert len(data["parsed_events"]) == 2
        assert len(data["troubleshooting_reports"]) >= 1

    def test_audit_history_endpoint(self, client):
        res = client.get("/troubleshoot/audit?limit=5")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_console_endpoint(self, client):
        res = client.get("/console")
        assert res.status_code == 200
        assert "Vendor-Aware Troubleshooting" in res.text

    def test_console_slash_endpoint(self, client):
        res = client.get("/console/")
        assert res.status_code == 200
        assert "Vendor-Aware Troubleshooting" in res.text
