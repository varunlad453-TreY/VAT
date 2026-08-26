# Hybrid RAG & Vector Search Engine

**Canonical Specification of Dense pgvector & Sparse BM25 Search Mechanics**

---

## 1. Hybrid Search Architecture

VAT uses a **Dense + Sparse Hybrid Retrieval** model to overcome the limitations of pure vector similarity in technical networking contexts.

```
                  [ USER QUERY / RAW SYSLOG STRING ]
                                   │
                ┌──────────────────┴──────────────────┐
                ▼                                     ▼
      [ DENSE VECTOR PIPELINE ]             [ SPARSE LEXICAL PIPELINE ]
      • Model: all-MiniLM-L6-v2             • Parser: tsvector ('english')
      • 384-dimensional dense float         • Inverted index: GIN
      • Index: HNSW (vector_cosine_ops)     • Ranking: ts_rank_cd
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

## 2. Dense Vector Pipeline (pgvector HNSW)

- **Embedding Model**: `all-MiniLM-L6-v2` (via `sentence-transformers`).
- **Vector Dimension**: `384` floating-point numbers.
- **Normalization**: Normalized L2 Euclidean distance ($\|\mathbf{v}\| \approx 1.0$).
- **HNSW Cosine Operator**: `<=>` (Cosine Distance, where similarity is `1 - distance`).

### SQL Dense Component
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

## 3. Sparse Lexical Pipeline (PostgreSQL tsvector)

In networking telemetry, specific error codes (e.g. `%OSPF-5-ADJCHG`, `%BGP-5-ADJCHANGE`, `EDGE_LINK_DEGRADATION`, `VCMP`, `EXSTART`) must match with exact lexical precision. 

- **Token Storage**: `tsv_content tsvector` column automatically generated on insert.
- **Index**: `GIN(tsv_content)` for sub-millisecond keyword lookup.
- **Ranking Function**: `ts_rank_cd(tsv_content, plainto_tsquery('english', $2))` which penalizes distance between query terms in document chunks.

---

## 4. Documentation Chunking & ETL Specifications

The ETL pipeline (`scripts/ingest_vendor_docs.py`) applies the following chunking parameters:

- **Target Chunk Size**: 400 words.
- **Overlap Window**: 50 words (preserves context across sentence boundaries).
- **Metadata Fields**: `source_url`, `title`, `vendor`, `product_family`, `protocol`, `error_codes`.

---

## 5. Offline Fallback Corpus (`ENTERPRISE_FALLBACK_CORPUS`)

If PostgreSQL or the embedding model is unavailable, `VectorService` executes in-memory deterministic hybrid scoring across pre-indexed vendor troubleshooting trees covering:
1. Cisco IOS-XR / IOS-XE BGP Hold-Timer Expiry
2. Cisco IOS-XE OSPF EXSTART MTU Mismatch
3. Juniper Junos BGP RPD Peer Reset & Idle Timeout
4. VMware VeloCloud SD-WAN VCMP Overlay Loss & PMTUD Blackhole
5. Arista EOS EVPN/MLAG Split-Brain Isolation
