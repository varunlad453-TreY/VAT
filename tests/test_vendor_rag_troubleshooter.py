"""
Unit & Integration Tests for Vendor-Aware AI Troubleshooter (True RAG)
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.troubleshoot import (
    ResolutionStep,
    TroubleshootRequest,
    TroubleshootResponse,
    VendorDocCitation,
)
from backend.services.ai_service import ai_service
from backend.services.vector_service import vector_service
from scripts.ingest_vendor_docs import chunk_text, generate_embeddings


@pytest.fixture
def client():
    return TestClient(app)


class TestVectorEmbeddingAndChunking:
    """Test text preprocessing, chunking, and dense vector generation."""

    def test_text_chunking_with_overlap(self):
        sample_text = "word " * 600
        chunks = chunk_text(sample_text, chunk_size=400, overlap=50)
        assert len(chunks) >= 2
        # Check first chunk size
        assert len(chunks[0].split()) == 400

    def test_vector_embedding_dimension(self):
        sample = "OSPF neighbor stuck in EXSTART due to MTU mismatch"
        embeddings = generate_embeddings([sample])
        assert len(embeddings) == 1
        assert len(embeddings[0]) == 384
        # Verify normalization (L2 norm ≈ 1.0)
        norm = sum(x * x for x in embeddings[0]) ** 0.5
        assert pytest.approx(norm, 0.01) == 1.0


class TestVectorService:
    """Test vector similarity search functionality."""

    @pytest.mark.asyncio
    async def test_find_relevant_docs_fallback_corpus(self):
        query = "%OSPF-5-ADJCHG: Nbr 192.168.1.2 on GigabitEthernet0/0/1 from EXSTART to DOWN"
        docs = await vector_service.find_relevant_docs(query, limit=3, vendor="cisco")
        
        assert len(docs) > 0
        assert len(docs) <= 3
        # Top match should be the Exstart / MTU document
        top_doc = docs[0]
        assert "13684" in top_doc["source_url"] or "exstart" in top_doc["chunk_text"].lower()
        assert top_doc["similarity"] >= 0.70

    @pytest.mark.asyncio
    async def test_find_relevant_docs_with_mocked_db(self):
        mock_db = AsyncMock()
        mock_db.is_connected = AsyncMock(return_value=True)
        mock_db.fetch = AsyncMock(return_value=[
            {
                "id": 1,
                "source_url": "https://www.cisco.com/c/en/us/support/docs/ip/open-shortest-path-first-ospf/13684-12.html",
                "title": "Troubleshoot OSPF Neighbors Stuck in Exstart/Exchange State",
                "vendor": "cisco",
                "chunk_text": "In Exstart state, routers negotiate master-slave and exchange DBD packets. MTU mismatch causes packet drop.",
                "similarity": 0.93,
            }
        ])

        with patch("backend.services.vector_service.db", mock_db):
            docs = await vector_service.find_relevant_docs("MTU mismatch OSPF EXSTART", limit=1)
            assert len(docs) == 1
            assert docs[0]["similarity"] == 0.93
            assert docs[0]["vendor"] == "cisco"


class TestAIServiceRAGSynthesis:
    """Test end-to-end RAG diagnostic and resolution playbook synthesis."""

    @pytest.mark.asyncio
    async def test_suggest_resolution_ospf_exstart_issue(self):
        raw_log = (
            "%OSPF-5-ADJCHG: Process 1, Nbr 192.168.1.2 on GigabitEthernet0/0/1 "
            "from EXSTART to DOWN, Neighbor Down: Too many retransmissions"
        )
        req = TroubleshootRequest(
            incident_id="inc-ospf-001",
            device_id="Core-Router-East",
            vendor="cisco",
            raw_logs=raw_log,
        )

        response = await ai_service.suggest_resolution_from_docs(req)

        assert isinstance(response, TroubleshootResponse)
        assert response.incident_id == "inc-ospf-001"
        assert "EXSTART" in response.diagnosis.upper() or "MTU" in response.diagnosis.upper()
        assert response.confidence_score >= 0.85
        assert len(response.resolution_steps) >= 2 or len(response.remediation_commands) >= 2
        assert len(response.cited_vendor_docs) > 0

        # Check resolution step CLI commands
        commands = [s.command for s in response.resolution_steps if s.command]
        assert any("show ip ospf" in c or "show interface" in c or "ip mtu" in c or "mtu-ignore" in c for c in commands)

        # Check citations
        citations = response.cited_vendor_docs
        assert any("cisco.com" in c.source_url for c in citations)


class TestFastAPIEndpoints:
    """Test REST API routes."""

    def test_health_check_endpoint(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert "status" in data
        assert "vendor-aware-troubleshooter" in data["service"]

    def test_root_endpoint(self, client):
        res = client.get("/")
        assert res.status_code == 200
        data = res.json()
        assert "troubleshoot_url" in data

    def test_troubleshoot_endpoint_success(self, client):
        payload = {
            "device_id": "Edge-Switch-01",
            "vendor": "cisco",
            "raw_logs": "%OSPF-5-ADJCHG: Process 100, Nbr 10.0.0.2 on GigabitEthernet0/1 from EXSTART to DOWN",
        }
        res = client.post("/troubleshoot", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "diagnosis" in data
        assert "resolution_steps" in data
        assert len(data["resolution_steps"]) > 0
        assert len(data["cited_vendor_docs"]) > 0

    def test_troubleshoot_endpoint_validation_error(self, client):
        # Empty raw_logs should return 422
        payload = {
            "device_id": "Edge-Switch-01",
            "raw_logs": "   ",
        }
        res = client.post("/troubleshoot", json=payload)
        assert res.status_code == 422

    def test_list_vendor_sources_endpoint(self, client):
        res = client.get("/troubleshoot/sources?query=OSPF+EXSTART&limit=2")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) <= 2
        if data:
            assert "source_url" in data[0]
            assert "similarity_score" in data[0]
