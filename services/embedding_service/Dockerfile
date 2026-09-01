# ==============================================================================
# VAT Dedicated Embedding Worker Microservice Dockerfile
# Optimized for GPU/CPU Inference with non-root security and model pre-caching
# ==============================================================================

FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Pre-download and cache model in image for air-gapped / fast startup
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Final Runtime Image
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8001 \
    EMBEDDING_MODEL=all-MiniLM-L6-v2 \
    EMBEDDING_DIMENSION=384

# Copy installed packages and pre-cached model from builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /root/.cache /root/.cache
COPY main.py .

# Healthcheck probe
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2", "--access-log"]
