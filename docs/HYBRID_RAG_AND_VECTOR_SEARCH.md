# Hybrid RAG & Vector Search Engine

**Canonical Specification of Dense Vector, Sparse BM25 & Qdrant Search Mechanics**

---

## 1. Hybrid Search Architecture

VAT uses a **Dense + Sparse Hybrid Retrieval** model with Reciprocal Rank Fusion (RRF) to overcome the limitations of pure vector similarity in technical carrier networking contexts:

```
                  [ USER QUERY / RAW SYSLOG STRING ]
                                   │
                ┌──────────────────┴──────────────────┐
                ▼                                     ▼
      [ DENSE VECTOR PIPELINE ]             [ SPARSE LEXICAL PIPELINE ]
      • Model: all-MiniLM-L6-v2             • Parser: tsvector ('english')
      • 384-dimensional dense float         • Inverted index: GIN
      • Engine: Qdrant / pgvector HNSW      • Ranking: ts_rank_cd
      • Weight: 65% (0.65)                  • Weight: 35% (0.35)
                │                                     │
                └──────────────────┬──────────────────┘
                                   │
                                   ▼
          [ RECIPROCAL RANK FUSION (RRF) & HYBRID SCORE MERGE ]
            Score = (Dense_Sim * 0.65) + (Sparse_Score * 0.35)
                                   │
                                   ▼
         [ TOP-K RANKED GROUNDED VENDOR DOCUMENTATION CITATIONS ]
```

---

## 2. Decoupled GPU Embedding Worker (`services/embedding_service`)

Dense vector generation is decoupled from the main FastAPI server into a dedicated microservice:

- **Location**: `services/embedding_service/main.py`
- **Network Port**: `8001`
- **Model**: `all-MiniLM-L6-v2` (via PyTorch & `sentence-transformers`)
- **Vector Dimension**: `384` floating-point numbers
- **Normalization**: Normalized L2 Euclidean distance ($\|\mathbf{v}\|_2 \approx 1.0$)
- **Client Implementation**: `backend/infrastructure/ai/remote_embedding_client.py`
  - Sends batched POST requests to `http://localhost:8001/embed`.
  - Automatically handles connection retries and falls back to local in-process generation or deterministic SHA-256 normalized vector hashing if the embedding service is offline.

---

## 3. Dense Vector Storage: Qdrant & PostgreSQL pgvector

VAT supports polyglot vector persistence via clean repository interfaces (`IVectorRepository`):

### 3.1 Qdrant Vector Repository (`QdrantVectorRepository`)
- **Collection**: `vat_vendor_knowledge`
- **Distance Metric**: Cosine Distance
- **Metadata Filtering**: Filter by `vendor` and `protocol` payloads prior to ANN candidate scoring.
- **Port**: `6333` (HTTP) / `6334` (gRPC).

### 3.2 PostgreSQL pgvector Repository (`PgVectorRepository`)
- **Table**: `vendor_knowledge`
- **Index**: `HNSW (embedding vector_cosine_ops)`
- **Query Operator**: `<=>` (Cosine Distance, where `similarity = 1 - distance`):
  ```sql
  WITH dense_search AS (
      SELECT 
          id, source_url, title, vendor, protocol, chunk_text, 
          ROW_NUMBER() OVER (ORDER BY embedding <=> $1::vector) as dense_rank,
          1 - (embedding <=> $1::vector) AS dense_similarity
      FROM vendor_knowledge
      WHERE ($3::text IS NULL OR vendor = $3)
        AND ($4::text IS NULL OR protocol = $4)
      LIMIT 20
  )
  ```

---

## 4. Sparse Lexical Pipeline (PostgreSQL tsvector)

In carrier network operations, exact tokens (e.g. `%OSPF-5-ADJCHG`, `%BGP-5-ADJCHANGE`, `EDGE_LINK_DEGRADATION`, `VCMP`, `EXSTART`) require exact lexical matching:

- **Token Storage**: `tsv_content tsvector` column automatically maintained on insert.
- **Index**: `GIN(tsv_content)` for sub-millisecond keyword lookup.
- **Ranking Function**: `ts_rank_cd(tsv_content, plainto_tsquery('english', $2))` which measures token frequency and word-distance proximity.

---

## 5. Documentation Chunking & ETL Pipeline

The ETL pipeline (`backend/scripts/ingest_vendor_docs.py` and `scripts/ingest_vendor_docs.py`) applies standard chunking parameters:

- **Target Chunk Size**: 400 words.
- **Overlap Window**: 50 words (preserves context across sentence boundaries).
- **Metadata Fields**: `source_url`, `title`, `vendor`, `product_family`, `protocol`, `error_codes`.

---

## 6. Air-Gapped Resilient Fallback Corpus (`ENTERPRISE_FALLBACK_CORPUS`)

If Qdrant, PostgreSQL, or the embedding microservice is offline, `InMemoryVectorRepository` (`backend/infrastructure/repositories/in_memory_repository.py`) executes in-memory deterministic hybrid scoring across pre-indexed vendor troubleshooting trees covering:

1. **Cisco IOS-XR / IOS-XE**: BGP Hold-Timer Expiry & Flapping.
2. **Cisco IOS-XE**: OSPF EXSTART MTU Mismatch.
3. **Juniper Junos**: BGP RPD Peer Reset & Idle Timeout.
4. **VMware VeloCloud**: SD-WAN VCMP Overlay Loss & PMTUD Blackhole.
5. **Arista EOS**: EVPN / MLAG Split-Brain Peer Isolation.
