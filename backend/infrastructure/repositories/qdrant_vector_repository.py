"""
Infrastructure Adapter: Qdrant Distributed Vector Repository
High-throughput HNSW vector similarity search with payload filtering for Carrier RAG.
"""

import logging
from typing import Any, Dict, List, Optional
import httpx

from backend.application.ports.vector_repository import IVectorRepository
from backend.infrastructure.adapters.remote_embedding_client import embedding_client
from backend.infrastructure.repositories.in_memory_repository import InMemoryVectorRepository
from config.settings import get_settings

logger = logging.getLogger("vat-qdrant-repo")


class QdrantVectorRepository(IVectorRepository):
    """Distributed Vector Database Adapter using Qdrant with air-gapped fallback."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        collection_name: Optional[str] = None,
    ) -> None:
        settings = get_settings()
        self._host = host or settings.qdrant_host
        self._port = port or settings.qdrant_port
        self._collection = collection_name or settings.qdrant_collection_name
        self._base_url = f"http://{self._host}:{self._port}"
        self._fallback_repo = InMemoryVectorRepository()

    async def find_relevant_docs(
        self,
        query_text: str,
        limit: int = 3,
        vendor: Optional[str] = None,
        protocol: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes distributed vector similarity search against Qdrant collection with
        payload filters. Falls back cleanly to in-memory fallback corpus if Qdrant is unavailable.
        """
        query_vector = await embedding_client.embed_text(query_text)
        url = f"{self._base_url}/collections/{self._collection}/points/search"

        # Build payload filter
        must_filters = []
        if vendor:
            must_filters.append({"key": "vendor", "match": {"value": vendor.lower()}})
        if protocol:
            must_filters.append({"key": "protocol", "match": {"value": protocol.lower()}})

        payload: Dict[str, Any] = {
            "vector": query_vector,
            "limit": limit,
            "with_payload": True,
        }
        if must_filters:
            payload["filter"] = {"must": must_filters}

        try:
            async with httpx.AsyncClient(timeout=2.5) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    for pt in data.get("result", []):
                        pl = pt.get("payload", {})
                        results.append({
                            "id": pt.get("id"),
                            "title": pl.get("title", "Vendor Documentation"),
                            "source_url": pl.get("source_url", "https://support.vendor.com"),
                            "vendor": pl.get("vendor", vendor or "cisco"),
                            "protocol": pl.get("protocol", protocol or "general"),
                            "chunk_text": pl.get("chunk_text", ""),
                            "similarity": pt.get("score", 0.90),
                        })
                    if results:
                        return results
        except Exception as exc:
            logger.debug("Qdrant search fallback invoked (%s): %s", url, exc)

        # Resilient air-gapped fallback
        return await self._fallback_repo.find_relevant_docs(
            query_text=query_text,
            limit=limit,
            vendor=vendor,
            protocol=protocol,
        )

    async def index_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """Uploads and indexes text chunks into Qdrant collection."""
        url = f"{self._base_url}/collections/{self._collection}/points"
        points = []
        for idx, chunk in enumerate(chunks):
            vec = chunk.get("embedding") or await embedding_client.embed_text(chunk.get("chunk_text", ""))
            points.append({
                "id": chunk.get("id", idx + 1),
                "vector": vec,
                "payload": {
                    "title": chunk.get("title"),
                    "source_url": chunk.get("source_url"),
                    "vendor": chunk.get("vendor"),
                    "protocol": chunk.get("protocol"),
                    "chunk_text": chunk.get("chunk_text"),
                },
            })

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.put(url, json={"points": points})
                if response.status_code == 200:
                    return len(points)
        except Exception as exc:
            logger.debug("Qdrant indexing fallback invoked: %s", exc)

        return await self._fallback_repo.index_chunks(chunks)

    def embed_text(self, text: str) -> List[float]:
        """Synchronous embedding accessor with fallback."""
        return embedding_client.embed_text_sync(text)

    async def is_healthy(self) -> bool:
        """Check if Qdrant service is active, with fallback health check."""
        url = f"{self._base_url}/readyz"
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    return True
        except Exception:
            pass
        return await self._fallback_repo.is_healthy()

