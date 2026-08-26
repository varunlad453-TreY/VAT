"""
Tests for Phase 4: Presentation Layer (FastAPI Controllers, Dependency Injection & WebSockets)
Validates REST API routes, DI container overrides, and real-time WebSocket streaming.
"""

import json
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.presentation.dependencies import get_vector_repository
from backend.infrastructure.repositories.in_memory_repository import InMemoryVectorRepository

client = TestClient(app)


# ══════════════════════════════════════════════════════════════════════════════
# 1. REST API Route & Dependency Injection Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestPresentationRESTControllers:
    """Test suite for Presentation Layer HTTP controllers."""

    def test_health_check_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "vendor-aware-troubleshooter-enterprise"
        assert "status" in data
        assert "database_connected" in data
        assert data["version"] == "2.0.0"

    def test_root_metadata_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "troubleshoot_url" in data
        assert "telemetry_url" in data
        assert "ws_telemetry_url" in data
        assert "ws_troubleshoot_url" in data

    def test_troubleshoot_endpoint_cisco_bgp(self):
        payload = {
            "raw_logs": "%BGP-5-ADJCHANGE: neighbor 10.10.10.1 Down - hold time expired",
            "device_id": "Core-Router-01",
            "vendor": "cisco",
            "protocol": "bgp",
        }
        response = client.post("/troubleshoot", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["vendor"] == "cisco"
        assert data["protocol"] == "bgp"
        assert len(data["pre_checks"]) == 3
        assert len(data["remediation_commands"]) == 2
        assert len(data["post_checks"]) == 2
        assert len(data["rollback_playbook"]) == 1
        assert data["risk_assessment"]["risk_level"] == "MEDIUM"
        assert len(data["cited_vendor_docs"]) >= 1

    def test_troubleshoot_endpoint_validation_empty_logs(self):
        response = client.post("/troubleshoot", json={"raw_logs": "   "})
        assert response.status_code == 422

    def test_troubleshoot_sources_endpoint(self):
        response = client.get("/troubleshoot/sources?vendor=cisco&protocol=ospf&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["vendor"] == "cisco"

    def test_troubleshoot_audit_endpoint(self):
        response = client.get("/troubleshoot/audit?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_telemetry_parse_endpoint(self):
        raw_log = "%MLAG-4-SPLIT_BRAIN: MLAG peer link down on Leaf-01"
        response = client.post(f"/telemetry/parse?raw_log={raw_log}")
        assert response.status_code == 200
        data = response.json()
        assert data["vendor"] == "arista"
        assert data["event_code"] == "%MLAG-4-SPLIT_BRAIN"
        assert data["protocol"] == "evpn"

    def test_telemetry_ingest_batch_endpoint(self):
        payload = {
            "logs": [
                "%BGP-5-ADJCHANGE: neighbor 10.10.10.1 Down",
                "%SYS-5-CONFIG_I: Configured from console by admin",
            ],
            "device_hint": "Border-GW-01",
            "auto_troubleshoot": True,
        }
        response = client.post("/telemetry/ingest", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total_received"] == 2
        assert len(data["parsed_events"]) == 2
        assert len(data["troubleshooting_reports"]) >= 1


# ══════════════════════════════════════════════════════════════════════════════
# 2. Dependency Injection Container Override Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestDependencyInjectionOverrides:
    """Test suite for DI container inversion of control."""

    def test_vector_repository_di_override(self):
        # Create a custom in-memory repository with a single unique chunk
        custom_corpus = [{
            "id": 999,
            "source_url": "https://custom-tac.carrier.net/doc1",
            "title": "Custom Carrier BGP Manual",
            "vendor": "cisco",
            "protocol": "bgp",
            "error_codes": ["%BGP-CUSTOM"],
            "chunk_text": "Custom TAC instructions for Carrier BGP.",
            "similarity": 0.99,
        }]
        custom_repo = InMemoryVectorRepository(corpus=custom_corpus)

        app.dependency_overrides[get_vector_repository] = lambda: custom_repo

        try:
            response = client.get("/troubleshoot/sources?vendor=cisco&protocol=bgp&limit=1")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == "Custom Carrier BGP Manual"
        finally:
            app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════════════════════
# 3. Real-Time WebSockets Streaming Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestPresentationWebSockets:
    """Test suite for Real-Time WebSockets streaming."""

    def test_websocket_telemetry_streaming(self):
        with client.websocket_connect("/ws/telemetry") as ws:
            # 1. Receive connection handshake
            init_msg = ws.receive_json()
            assert init_msg["type"] == "connection_established"

            # 2. Send raw telemetry log
            raw_log = "%OSPF-5-ADJCHG: Process 1, Nbr 192.168.1.2 on GigabitEthernet0/0/1 from EXSTART to DOWN"
            ws.send_text(raw_log)

            # 3. Receive normalized event
            resp = ws.receive_json()
            assert resp["type"] == "telemetry_event"
            assert resp["parsed"]["vendor"] == "cisco"
            assert resp["parsed"]["protocol"] == "ospf"
            assert resp["parsed"]["event_code"] == "%OSPF-5-ADJCHG"

    def test_websocket_troubleshoot_synthesis_progress(self):
        with client.websocket_connect("/ws/troubleshoot") as ws:
            # 1. Receive connection handshake
            init_msg = ws.receive_json()
            assert init_msg["type"] == "connection_established"

            # 2. Send troubleshooting request
            payload = json.dumps({
                "raw_logs": "%BGP-5-ADJCHANGE: neighbor 10.10.10.1 Down - hold time expired",
                "device_id": "Core-RT-01",
                "vendor": "cisco",
                "protocol": "bgp",
            })
            ws.send_text(payload)

            # 3. Receive progress stages
            msg1 = ws.receive_json()
            assert msg1["type"] == "progress"
            assert msg1["stage"] == "parsing"

            msg2 = ws.receive_json()
            assert msg2["type"] == "progress"
            assert msg2["stage"] == "parsed"
            assert msg2["vendor"] == "cisco"

            msg3 = ws.receive_json()
            assert msg3["type"] == "progress"
            assert msg3["stage"] == "retrieval"

            msg4 = ws.receive_json()
            assert msg4["type"] == "progress"
            assert msg4["stage"] == "retrieved_citations"

            msg5 = ws.receive_json()
            assert msg5["type"] == "progress"
            assert msg5["stage"] == "synthesizing"

            # 4. Receive complete runbook
            completed_msg = ws.receive_json()
            assert completed_msg["type"] == "runbook_completed"
            runbook = completed_msg["runbook"]
            assert runbook["vendor"] == "cisco"
            assert len(runbook["pre_checks"]) == 3
            assert len(runbook["remediation_commands"]) == 2
            assert len(runbook["post_checks"]) == 2
            assert len(runbook["rollback_playbook"]) == 1
