# Setup, Configuration & Deployment Guide

**Canonical Specification for Local Development and Production Deployment**

---

## 1. System Requirements

- **Operating System**: Linux (Ubuntu 22.04+ / RHEL 9), macOS, or Windows (via WSL2 or native PowerShell).
- **Python**: Version 3.10, 3.11, 3.12, 3.13, or 3.14.
- **Docker**: Docker Engine 24+ and Docker Compose v2 (required only for PostgreSQL pgvector container).
- **Memory**: Minimum 2 GB RAM (4 GB recommended when loading local SentenceTransformer models).

---

## 2. Environment Configuration Reference (`.env`)

```ini
# Service Identity
ENVIRONMENT=development
LOG_LEVEL=INFO

# PostgreSQL pgvector Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=vat
POSTGRES_USER=vat
POSTGRES_PASSWORD=vat_password
DATABASE_URL=postgresql://vat:vat_password@localhost:5432/vat

# Vector Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# LLM Inference (Optional: GitHub Models / Azure Inference / OpenAI)
GITHUB_TOKEN=
OPENAI_API_KEY=
AI_MODEL=gpt-4o-mini
AI_BASE_URL=https://models.inference.ai.azure.com
```

---

## 3. Local Installation & Startup

### Step 1: Clone Repository & Install Python Packages
```powershell
git clone <repository_url>
cd g:\VAT
python -m pip install -r requirements.txt
```

### Step 2: Launch PostgreSQL with pgvector (Optional)
```powershell
docker-compose up -d
```
Verify container health:
```powershell
docker ps --filter "name=vat-postgres"
```

### Step 3: Run Database Migrations / Schema Initialization
When using Docker Compose, schemas in `schemas/postgres/` are automatically mounted to `/docker-entrypoint-initdb.d` and initialized on first run. To manually execute schemas on an existing PostgreSQL database:
```powershell
psql -U vat -d vat -f schemas/postgres/01_vector_schema.sql
psql -U vat -d vat -f schemas/postgres/02_hybrid_vector_schema.sql
```

### Step 4: Index Vendor Manuals (Optional)
```powershell
python scripts/ingest_vendor_docs.py
```

### Step 5: Start FastAPI Application Server
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 4. Production Deployment Recommendations

- **Reverse Proxy**: Deploy behind NGINX, Cloudflare, or AWS ALB with TLS termination.
- **Process Manager**: Use `gunicorn` with `uvicorn.workers.UvicornWorker` or containerize via multi-stage Docker build.
- **Database High Availability**: Managed PostgreSQL (AWS Aurora PostgreSQL with pgvector, GCP Cloud SQL, or Azure Database for PostgreSQL).
- **Health Probing**: Configure load balancers to poll `GET /health` every 10 seconds.
