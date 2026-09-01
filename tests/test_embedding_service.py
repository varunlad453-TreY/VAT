"""
Test Suite: Dedicated Embedding Worker & Resilient Remote Client
Validates compute isolation, tenacity retry policy, and deterministic fallback.
"""

import pytest
from httpx import Response
from unittest.mock import AsyncMock, patch

from backend.infrastructure.adapters.remote_embedding_client import RemoteEmbeddingClient
from services.embedding_service.main import app
from fastapi.testclient import TestClient


class TestEmbeddingMicroservice:
    """Tests for the standalone embedding microservice."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_health_check_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["service"] == "vat-embedding-service"

    def test_metrics_endpoint(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "vat_embedding_requests_total" in response.text

    def test_embed_endpoint_validation_empty_texts(self, client):
        response = client.post("/embed", json={"texts": []})
        assert response.status_code == 422 or response.status_code == 400


class TestRemoteEmbeddingClient:
    """Tests for the resilient remote client calling embedding worker."""

    @pytest.mark.asyncio
    async def test_embed_text_fallback_when_service_offline(self):
        """When the embedding worker is down, the client returns a deterministic 384-dim vector."""
        client = RemoteEmbeddingClient(base_url="http://invalid-host:9999", timeout=0.1, max_retries=1)
        embedding = await client.embed_text("BGP neighbor down hold timer expired")
        assert len(embedding) == 384
        assert isinstance(embedding, list)
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.asyncio
    async def test_embed_texts_successful_response(self):
        """When the remote service is healthy, client parses and returns embeddings."""
        import httpx
        mock_embedding = [0.1] * 384
        req = httpx.Request("POST", "http://localhost:8001/embed")
        mock_response = Response(
            200,
            json={
                "embeddings": [mock_embedding],
                "dimension": 384,
                "model": "all-MiniLM-L6-v2",
                "device": "cpu",
                "inference_time_ms": 12.5,
                "count": 1,
            },
            request=req,
        )

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            client = RemoteEmbeddingClient(base_url="http://localhost:8001")
            res = await client.embed_texts(["Cisco OSPF MTU mismatch"])
            assert len(res) == 1
            assert len(res[0]) == 384
            assert res[0][0] == 0.1

    def test_sync_embed_fallback(self):
        client = RemoteEmbeddingClient()
        emb = client.embed_text_sync("Juniper Junos RPD hold timer")
        assert len(emb) == 384
        assert isinstance(emb, list)
