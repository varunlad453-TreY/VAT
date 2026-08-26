# Production Multi-Stage Dockerfile for VAT Backend (FastAPI Clean Architecture)
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY backend ./backend
COPY config ./config
COPY schemas ./schemas
COPY docs ./docs
COPY scripts ./scripts
COPY frontend ./frontend

# Create non-root system user for carrier security
RUN addgroup --system vat && adduser --system --group vat
USER vat

EXPOSE 8000

# Run FastAPI Clean Architecture Application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
