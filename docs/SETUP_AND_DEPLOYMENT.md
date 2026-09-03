# Setup, Configuration & Deployment Guide

**Canonical Specification for Local Development, Container Stacks & Kubernetes Rollout**

---

## 1. System Requirements & Prerequisites

- **Operating System**: Linux (Ubuntu 22.04+ / RHEL 9), macOS, or Windows (via native PowerShell or WSL2).
- **Python**: Version 3.10, 3.11, 3.12, 3.13, or 3.14.
- **Node.js**: Version 18.0+ and `npm` (required for modern Next.js frontend).
- **Docker**: Docker Engine 24+ and Docker Compose v2 (required for polyglot persistence).
- **Kubectl & Helm**: Kubernetes CLI and Helm 3.12+ (for cluster deployment).
- **Tilt & vcluster** (Optional for DevEx): Tilt 0.33+ and Loft vcluster CLI.

---

## 2. Environment Variables Reference (`.env`)

Configure the following parameters in `.env` (template in `.env.example`). Never commit production credentials to source control:

| Variable Name | Default Value | Purpose |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `development` | Deployment environment (`development`, `staging`, `production`). |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host. |
| `POSTGRES_PORT` | `5432` | PostgreSQL port. |
| `POSTGRES_DB` | `vat_troubleshooter` | Database name. |
| `POSTGRES_USER` | `postgres` | Database username. |
| `POSTGRES_PASSWORD` | `postgres` | Database password. |
| `QDRANT_HOST` | `localhost` | Qdrant vector database host. |
| `QDRANT_PORT` | `6333` | Qdrant HTTP API port. |
| `REDPANDA_BROKERS` | `localhost:9092` | Comma-separated Kafka/Redpanda bootstrap brokers. |
| `CLICKHOUSE_HOST` | `localhost` | ClickHouse server host. |
| `CLICKHOUSE_HTTP_PORT`| `8123` | ClickHouse HTTP interface port. |
| `REDIS_HOST` | `localhost` | Redis caching and pub/sub host. |
| `REDIS_PORT` | `6379` | Redis port. |
| `EMBEDDING_SERVICE_URL`| `http://localhost:8001`| HTTP endpoint of decoupled embedding microservice. |
| `EMBEDDING_MODEL_NAME`| `all-MiniLM-L6-v2` | SentenceTransformer embedding model identifier. |
| `OPENAI_API_KEY` | *(empty)* | Optional. If provided, enables cloud LLM playbook synthesis. |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:8000` | Allowed CORS origins for REST and WebSockets. |

---

## 3. Local Development Startup (Multi-Service Stack)

### Step 1: Install Python Environment
```bash
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2: Start Polyglot Persistence (Docker Compose)
Launch PostgreSQL (with pgvector), Redpanda, ClickHouse, and Redis:
```bash
docker-compose up -d
```
*Resilience Note: If Docker is unavailable, the application starts with 100% functionality using its embedded in-memory fallback corpus and deterministic synthesizer.*

### Step 3: Start Decoupled Embedding Worker (Port 8001)
Open a dedicated terminal session:
```bash
python -m uvicorn services.embedding_service.main:app --host 0.0.0.0 --port 8001
```

### Step 4: Start Backend Application Server (Port 8000)
Open a dedicated terminal session:
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 5: Start Modern Next.js Frontend (Port 3000)
Open a dedicated terminal session:
```bash
cd frontend
npm install
npm run dev
```

### Step 6: Verify Endpoints
- **Modern NOC Application**: [http://localhost:3000](http://localhost:3000)
- **High-Density Legacy Console**: [http://localhost:8000/console](http://localhost:8000/console)
- **Interactive Swagger REST Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Embedding Worker Metrics**: [http://localhost:8001/metrics](http://localhost:8001/metrics)

---

## 4. Live Cloud-Native Development via Tilt

For rapid local feedback synchronized directly into Kubernetes without Docker image rebuilds:

```bash
# Start all microservices, live code synchronization, and port forwards:
tilt up
```

Tilt watches `backend/` and `frontend/` source trees, compiling changes and pushing live updates into running pods in **< 2.0 seconds**.

---

## 5. Kubernetes Production Deployment (`k8s/`)

### 5.1 Staged Infrastructure Components
The production Kubernetes architecture is organized into declarative manifests:

```
k8s/
├── vector/                     # Vector Syslog Collector DaemonSet
├── redpanda/                   # Redpanda StatefulSet (3 Replicas, Kafka API)
├── clickhouse/                 # ClickHouse Analytical StatefulSet
├── qdrant/                     # Qdrant Vector Search StatefulSet
├── embedding-worker/           # Decoupled Embedding Deployment, HPA, PDB
├── frontend/                   # Next.js Deployment, Service, and Ingress
├── gitops/                     # ArgoCD ApplicationSets for automated sync
├── chaos/                      # Chaos Mesh schedules & network partition tests
├── security/                   # Istio STRICT mTLS, Vault/ESO, Postgres RLS, ClickHouse RBAC
├── finops/                     # KEDA GPU scale-to-zero, Karpenter Spot fleets
├── devex/                      # Loft vcluster templates & sync bridges
└── disaster-recovery/          # Redpanda MirrorMaker 2, Postgres CNPG, Route53 failover
```

### 5.2 Progressive Staged Rollout Sequence

Execute during scheduled cluster maintenance windows:

```bash
# 1. Apply Security Mesh & Namespaces
kubectl apply -f k8s/security/mesh/namespaces.yaml
helm upgrade --install istio-base istio/base -n istio-system
helm upgrade --install istiod istio/istiod -n istio-system -f k8s/security/mesh/istio-helm-values.yaml
kubectl apply -f k8s/security/mesh/peer-authentication.yaml
kubectl apply -f k8s/security/mesh/authorization-policies.yaml

# 2. Deploy Dynamic Secrets & Database RBAC
helm upgrade --install external-secrets external-secrets/external-secrets -n external-secrets -f k8s/security/secrets/eso-helm-values.yaml
kubectl apply -f k8s/security/secrets/vault-secret-store.yaml
kubectl apply -f k8s/security/secrets/

# 3. Deploy Streaming & Persistence Data Plane
kubectl apply -f k8s/redpanda/
kubectl apply -f k8s/clickhouse/
kubectl apply -f k8s/qdrant/
kubectl apply -f k8s/vector/

# 4. Deploy Compute Elasticity & Workloads
helm upgrade --install keda kedacore/keda -n keda -f k8s/finops/keda/keda-helm-values.yaml
kubectl apply -f k8s/finops/keda/
kubectl apply -f k8s/finops/karpenter/
kubectl apply -f k8s/embedding-worker/
kubectl apply -f k8s/frontend/

# 5. Configure Disaster Recovery (Standby Region)
kubectl apply -f k8s/disaster-recovery/redpanda-mirroring.yaml
kubectl apply -f k8s/disaster-recovery/postgres-cnpg-cluster-dr.yaml
kubectl apply -f k8s/disaster-recovery/clickhouse-keeper-dr.yaml
kubectl apply -f k8s/disaster-recovery/route53-failover-policy.yaml
```
