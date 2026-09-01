"""
Infrastructure Adapter: Remote Embedding Client
Asynchronous HTTP client calling dedicated GPU/CPU embedding worker with Tenacity retry policy
and deterministic fallback for air-gapped resilience.
"""

import hashlib
import logging
import math
from typing import List, Optional

import httpx
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import get_settings

logger = logging.getLogger(__name__)


class RemoteEmbeddingClient:
    """Non-blocking, resilient client for remote SentenceTransformers embedding worker."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.embedding_service_url).rstrip("/")
        self._timeout = timeout or settings.embedding_timeout_seconds
        self._max_retries = max_retries or settings.embedding_max_retries
        self._dimension = settings.embedding_dimension

    def _deterministic_fallback(self, text: str) -> List[float]:
        """Generates normalized 384-dimensional vector deterministically from text."""
        vec = []
        clean_text = text.lower().strip()
        for i in range(self._dimension):
            h = hashlib.sha256(f"{clean_text}_{i}".encode("utf-8")).hexdigest()
            val = (int(h[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0
            vec.append(val)
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Asynchronously embed batch of texts using remote GPU/CPU embedding worker.
        Retries up to max_retries with exponential backoff via Tenacity.
        Falls back seamlessly to deterministic vectors on connection failure.
        """
        if not texts:
            return []

        url = f"{self._base_url}/embed"
        payload = {"texts": texts, "normalize": True}

        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self._max_retries),
                wait=wait_exponential(multiplier=0.1, min=0.1, max=0.5),
                retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError)),
                reraise=True,
            ):
                with attempt:
                    async with httpx.AsyncClient(timeout=self._timeout) as client:
                        response = await client.post(url, json=payload)
                        response.raise_for_status()
                        data = response.json()
                        return data.get("embeddings", [self._deterministic_fallback(t) for t in texts])
        except Exception as exc:
            logger.warning(
                "Remote embedding service unavailable at %s (%s). Falling back to deterministic vector generation.",
                url,
                exc,
            )
            return [self._deterministic_fallback(t) for t in texts]

    async def embed_text(self, text: str) -> List[float]:
        """Asynchronously embeds single text."""
        results = await self.embed_texts([text])
        return results[0] if results else self._deterministic_fallback(text)

    def embed_text_sync(self, text: str) -> List[float]:
        """Synchronous embedding accessor using deterministic fallback."""
        return self._deterministic_fallback(text)


# Global singleton instance
embedding_client = RemoteEmbeddingClient()
