"""
VAT Embedding Microservice
Dedicated standalone GPU/CPU-optimized microservice for high-throughput sentence-transformers inference.
Provides OpenTelemetry tracing and Prometheus metrics.
"""

import logging
import os
import sys
import time
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("vat-embedding-service")

# Global model state
_model = None
_device = "cpu"
_model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
_embedding_dim = int(os.getenv("EMBEDDING_DIMENSION", "384"))

# Metrics counters
_request_count = 0
_total_inference_time_ms = 0.0


def init_model():
    """Initializes and warms up the sentence-transformers model."""
    global _model, _device
    try:
        import torch
        from sentence_transformers import SentenceTransformer

        if torch.cuda.is_available():
            _device = "cuda"
            logger.info("CUDA GPU detected. Using device: %s (%s)", _device, torch.cuda.get_device_name(0))
        else:
            _device = "cpu"
            # Optimize CPU thread allocation
            num_threads = max(1, os.cpu_count() or 2)
            torch.set_num_threads(num_threads)
            logger.info("CUDA not available. Using CPU with %d threads.", num_threads)

        logger.info("Loading SentenceTransformer model '%s' onto device '%s'...", _model_name, _device)
        _model = SentenceTransformer(_model_name, device=_device)

        # Warmup model with dummy batch
        warmup_texts = ["BGP neighbor down hold timer expired", "OSPF MTU mismatch exstart state"]
        _ = _model.encode(warmup_texts, show_progress_bar=False, convert_to_numpy=True)
        logger.info("SentenceTransformer model '%s' loaded and warmed up successfully.", _model_name)
    except Exception as exc:
        logger.error("Failed to initialize SentenceTransformer model: %s", exc, exc_info=True)
        _model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for model loading and resource cleanup."""
    init_model()
    yield
    logger.info("Shutting down VAT Embedding Microservice...")


app = FastAPI(
    title="VAT Embedding Microservice",
    version="1.0.0",
    description="High-throughput dedicated vector embedding service for VAT Enterprise",
    lifespan=lifespan,
)


class EmbedRequest(BaseModel):
    texts: List[str] = Field(..., description="List of raw text strings to embed", min_length=1)
    normalize: bool = Field(default=True, description="L2-normalize output embeddings")


class EmbedResponse(BaseModel):
    embeddings: List[List[float]] = Field(..., description="List of float vector embeddings")
    dimension: int = Field(default=384, description="Vector dimension")
    model: str = Field(default="all-MiniLM-L6-v2", description="Embedding model name")
    device: str = Field(default="cpu", description="Inference compute device")
    inference_time_ms: float = Field(..., description="Compute duration in milliseconds")
    count: int = Field(..., description="Number of embeddings generated")


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Readiness and Liveness probe endpoint."""
    return {
        "status": "healthy" if _model is not None else "degraded",
        "service": "vat-embedding-service",
        "model": _model_name,
        "device": _device,
        "model_loaded": _model is not None,
    }


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus telemetry scrape endpoint."""
    avg_latency = (_total_inference_time_ms / _request_count) if _request_count > 0 else 0.0
    metrics_payload = f"""# HELP vat_embedding_requests_total Total number of embedding requests processed
# TYPE vat_embedding_requests_total counter
vat_embedding_requests_total {_request_count}

# HELP vat_embedding_inference_time_ms_total Total inference latency in milliseconds
# TYPE vat_embedding_inference_time_ms_total counter
vat_embedding_inference_time_ms_total {_total_inference_time_ms:.2f}

# HELP vat_embedding_avg_latency_ms Average inference latency in milliseconds
# TYPE vat_embedding_avg_latency_ms gauge
vat_embedding_avg_latency_ms {avg_latency:.2f}
"""
    return Response(content=metrics_payload, media_type="text/plain; version=0.0.4")


@app.post("/embed", response_model=EmbedResponse)
async def generate_embeddings(payload: EmbedRequest):
    """Generates batch embeddings asynchronously off the main application tier."""
    global _request_count, _total_inference_time_ms

    if _model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding model is not initialized",
        )

    if not payload.texts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Texts list cannot be empty",
        )

    t0 = time.perf_counter()
    try:
        # Generate embeddings
        raw_embeddings = _model.encode(
            payload.texts,
            normalize_embeddings=payload.normalize,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        embeddings_list = [emb.tolist() for emb in raw_embeddings]
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        # Update metrics
        _request_count += len(payload.texts)
        _total_inference_time_ms += elapsed_ms

        return EmbedResponse(
            embeddings=embeddings_list,
            dimension=len(embeddings_list[0]) if embeddings_list else _embedding_dim,
            model=_model_name,
            device=_device,
            inference_time_ms=round(elapsed_ms, 2),
            count=len(embeddings_list),
        )
    except Exception as exc:
        logger.error("Error during embedding inference: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed: {str(exc)}",
        )
