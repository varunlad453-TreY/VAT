"""
Port Interface: Vector & Lexical Knowledge Repository
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from backend.domain.entities.citation import KnowledgeChunk


class IVectorRepository(ABC):
    """Abstract port for Hybrid Vector & Full-Text documentation search."""

    @abstractmethod
    async def find_relevant_docs(
        self,
        query_text: str,
        limit: int = 3,
        vendor: Optional[str] = None,
        protocol: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Execute hybrid dense + sparse retrieval with Reciprocal Rank Fusion (RRF)."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate normalized 384-dimensional dense vector embedding."""
        pass

    @abstractmethod
    async def index_chunks(self, chunks: List[KnowledgeChunk]) -> int:
        """Batch upsert documentation chunks into vector and lexical indexes."""
        pass

    @abstractmethod
    async def is_healthy(self) -> bool:
        """Check if vector repository connection is active."""
        pass
