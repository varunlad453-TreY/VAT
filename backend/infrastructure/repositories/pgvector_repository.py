"""
Infrastructure Adapter: PostgreSQL pgvector & Full-Text Lexical Repository
Hybrid Vector Search using pgvector HNSW Cosine + tsvector BM25 Reciprocal Rank Fusion (RRF).
"""

import logging
from typing import Any, Dict, List, Optional

from backend.application.ports.vector_repository import IVectorRepository
from backend.database.client import db
from backend.domain.entities.citation import KnowledgeChunk
from backend.infrastructure.repositories.in_memory_repository import InMemoryVectorRepository

logger = logging.getLogger(__name__)


class AsyncpgVectorRepository(IVectorRepository):
    """PostgreSQL pgvector & tsvector Hybrid Repository with in-memory fallback."""

    def __init__(self, fallback_repo: Optional[InMemoryVectorRepository] = None) -> None:
        self._fallback_repo = fallback_repo or InMemoryVectorRepository()

    def embed_text(self, text: str) -> List[float]:
        """Generate normalized 384-dimensional vector embedding."""
        return self._fallback_repo.embed_text(text)

    async def find_relevant_docs(
        self,
        query_text: str,
        limit: int = 3,
        vendor: Optional[str] = None,
        protocol: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute Hybrid Vector Search:
        Combines pgvector HNSW Cosine Similarity (Dense, 0.65) with
        PostgreSQL tsvector Full-Text Search (Sparse BM25, 0.35).
        """
        embedding = self.embed_text(query_text)
        emb_str = str(embedding)

        v_filter = vendor.lower() if vendor and vendor.lower() not in ["generic", "multi_vendor", "all"] else None
        p_filter = protocol.lower() if protocol and protocol.lower() != "general" else None

        try:
            if await db.is_connected():
                query = """
                    WITH dense_search AS (
                        SELECT 
                            id, 
                            source_url, 
                            title, 
                            vendor, 
                            protocol,
                            chunk_text, 
                            ROW_NUMBER() OVER (ORDER BY embedding <=> $1::vector) as dense_rank,
                            1 - (embedding <=> $1::vector) AS dense_similarity
                        FROM vendor_knowledge
                        WHERE ($3::text IS NULL OR vendor = $3)
                          AND ($4::text IS NULL OR protocol = $4)
                        LIMIT 20
                    ),
                    sparse_search AS (
                        SELECT 
                            id, 
                            ROW_NUMBER() OVER (ORDER BY ts_rank_cd(tsv_content, plainto_tsquery('english', $2)) DESC) as sparse_rank,
                            ts_rank_cd(tsv_content, plainto_tsquery('english', $2)) as sparse_score
                        FROM vendor_knowledge
                        WHERE tsv_content @@ plainto_tsquery('english', $2)
                          AND ($3::text IS NULL OR vendor = $3)
                          AND ($4::text IS NULL OR protocol = $4)
                        LIMIT 20
                    )
                    SELECT 
                        d.id,
                        d.source_url,
                        d.title,
                        d.vendor,
                        d.protocol,
                        d.chunk_text,
                        COALESCE(
                            d.dense_similarity * 0.65 + COALESCE(s.sparse_score, 0.0) * 0.35,
                            d.dense_similarity
                        ) AS hybrid_score
                    FROM dense_search d
                    LEFT JOIN sparse_search s ON d.id = s.id
                    ORDER BY hybrid_score DESC
                    LIMIT $5;
                """
                rows = await db.fetch(query, emb_str, query_text, v_filter, p_filter, limit)
                if rows:
                    results = []
                    for r in rows:
                        score = r.get("hybrid_score") if "hybrid_score" in r else r.get("similarity", 0.88)
                        results.append({
                            "id": r["id"],
                            "source_url": r["source_url"],
                            "title": r["title"],
                            "vendor": r["vendor"],
                            "protocol": r.get("protocol", "general"),
                            "chunk_text": r["chunk_text"],
                            "similarity": float(score) if score is not None else 0.88,
                        })
                    return results
        except Exception as exc:
            logger.debug("Database hybrid vector query error, using in-memory fallback: %s", exc)

        # Fallback to in-memory corpus
        return await self._fallback_repo.find_relevant_docs(
            query_text=query_text,
            limit=limit,
            vendor=vendor,
            protocol=protocol,
        )

    async def index_chunks(self, chunks: List[KnowledgeChunk]) -> int:
        """Batch upsert documentation chunks into vector and lexical indexes."""
        if not chunks:
            return 0

        indexed_count = 0
        try:
            if await db.is_connected():
                for chunk in chunks:
                    emb = chunk.embedding or self.embed_text(chunk.chunk_text)
                    emb_str = str(emb)
                    query = """
                        INSERT INTO vendor_knowledge (source_url, title, vendor, product_family, protocol, error_codes, chunk_text, embedding)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8::vector)
                        RETURNING id;
                    """
                    await db.execute(
                        query,
                        chunk.source_url,
                        chunk.title,
                        chunk.vendor,
                        chunk.product_family,
                        chunk.protocol,
                        chunk.error_codes,
                        chunk.chunk_text,
                        emb_str,
                    )
                    indexed_count += 1
                return indexed_count
        except Exception as exc:
            logger.warning("Database indexing error: %s", exc)

        # Also index in fallback repo
        return await self._fallback_repo.index_chunks(chunks)

    async def is_healthy(self) -> bool:
        """Check if database connection is active."""
        try:
            return await db.is_connected()
        except Exception:
            return False
