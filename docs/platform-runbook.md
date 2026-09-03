# VAT Enterprise Platform Operational Runbooks (Day 3 SRE)

**Document ID:** `SRE-RUNBOOK-PLATFORM-001`  
**Classification:** Internal / Carrier-Grade Tier-1 Operations  
**Target Architecture:** VAT Enterprise (Redpanda, ClickHouse, PostgreSQL, Triton/Embedding Worker, K8s, ArgoCD)  
**SRE Mandate:** 99.999% Service Availability, Zero Alert Fatigue, Zero Tribal Knowledge  

---

## Runbook 1: Database Split-Brain (Blocked or Failed Alembic Migration)

### 1.1 Trigger & Detection
* **Alerts:** `ArgoCDSyncFailed`, `KubeJobFailed (vat-alembic-migration-baseline)`, `PostgresLockContentionWarning`
* **Symptoms:**
  * ArgoCD PreSync hook fails or hangs past 300s deadline.
  * Backend API pods crash on startup with `alembic.util.exc.CommandError: Target database is not up to date`.
  * Table lock contention on core relational tables (`vendors`, `devices`, `remediation_actions`).

### 1.2 Step-by-Step Resolution Procedure

#### Step 1: Terminate the Blocked Migration Job & Lock ArgoCD Sync
```bash
# Delete hung migration job to release pod-level handles
kubectl delete job vat-alembic-migration-baseline -n vat-system --ignore-not-found=true

# Pause ArgoCD auto-sync to avoid re-triggering the PreSync hook during triage
argocd app set vat-enterprise --sync-policy manual
```

#### Step 2: Inspect and Kill Blocking Locks in PostgreSQL
```bash
# Connect to PostgreSQL primary and query for active DDL locks
kubectl exec -it -n vat-system deploy/vat-postgres -- psql -U vat_user -d vat_enterprise -c "
SELECT 
    pid, 
    now() - pg_stat_activity.query_start AS duration, 
    query, 
    state,
    wait_event_type,
    wait_event
FROM pg_stat_activity
WHERE state != 'idle' 
  AND (query ILIKE '%alembic%' OR query ILIKE '%ALTER TABLE%' OR query ILIKE '%CREATE INDEX%')
ORDER BY duration DESC;
"

# Forcefully terminate the blocking PID (replace <BLOCKING_PID> with actual PID from above query)
kubectl exec -it -n vat-system deploy/vat-postgres -- psql -U vat_user -d vat_enterprise -c "
SELECT pg_terminate_backend(<BLOCKING_PID>);
"
```

#### Step 3: Inspect Database Revision vs Codebase Revision
```bash
# Check the currently registered revision in PostgreSQL
kubectl exec -it -n vat-system deploy/vat-postgres -- psql -U vat_user -d vat_enterprise -c "
SELECT version_num FROM alembic_version;
"

# Query Alembic history from the application container to determine current HEAD
kubectl exec -it -n vat-system deploy/vat-backend -- python -m alembic history --verbose | head -n 25
```

#### Step 4: Reconcile Schema State & Stamp Alembic Version
* **Case A: DDL partially failed and database was left dirty:**
  Inspect the database tables manually, revert any uncommitted table alterations, then stamp the database to the last confirmed good revision `<LAST_GOOD_REVISION>`:
  ```bash
  kubectl exec -it -n vat-system deploy/vat-backend -- python -m alembic stamp <LAST_GOOD_REVISION>
  ```
* **Case B: Direct SQL emergency override (if Alembic CLI is unresponsive):**
  ```bash
  kubectl exec -it -n vat-system deploy/vat-postgres -- psql -U vat_user -d vat_enterprise -c "
  BEGIN;
  LOCK TABLE alembic_version IN ACCESS EXCLUSIVE MODE;
  DELETE FROM alembic_version;
  INSERT INTO alembic_version (version_num) VALUES ('<LAST_GOOD_REVISION>');
  COMMIT;
  "
  ```

#### Step 5: Dry-Run and Execute Clean Migration to HEAD
```bash
# Generate SQL script dry-run to verify DDL safety
kubectl exec -it -n vat-system deploy/vat-backend -- python -m alembic upgrade head --sql

# Apply migration directly
kubectl exec -it -n vat-system deploy/vat-backend -- python -m alembic upgrade head
```

#### Step 6: Verify and Re-enable ArgoCD Automated Sync
```bash
# Verify alembic_version matches head
kubectl exec -it -n vat-system deploy/vat-postgres -- psql -U vat_user -d vat_enterprise -c "SELECT version_num FROM alembic_version;"

# Re-enable automated sync in ArgoCD
argocd app set vat-enterprise --sync-policy automated --auto-prune --self-heal
argocd app sync vat-enterprise
```

---

## Runbook 2: Stream Poisoning (Redpanda DLQ Inspection & Replay)

### 2.1 Trigger & Detection
* **Alerts:** `RedpandaConsumerLagSpike`, `FlinkProcessorCrashLoop`, `DeadLetterQueueIngressRateHigh`
* **Symptoms:**
  * Ingestion pipeline consumer lag increases past 50,000 messages on `vat-telemetry-raw`.
  * Stream processing pods continuously crash due to JSON deserialization or unhandled syslog format exceptions.
  * Poison pill records diverted into `vat-telemetry-dlq`.

### 2.2 Step-by-Step Resolution Procedure

#### Step 1: Assess Consumer Lag and Topic Partitions
```bash
# Check lag across consumer groups
kubectl exec -it -n vat-system vat-redpanda-0 -c redpanda -- rpk group describe vat-telemetry-consumer-group

# Describe DLQ topic partitions and watermark offsets
kubectl exec -it -n vat-system vat-redpanda-0 -c redpanda -- rpk topic describe vat-telemetry-dlq
```

#### Step 2: Extract and Inspect Malformed Payloads from DLQ
```bash
# Sample last 5 poison pill records in JSON format
kubectl exec -it -n vat-system vat-redpanda-0 -c redpanda -- \
  rpk topic consume vat-telemetry-dlq --num 5 --format json > /tmp/poison_pill_sample.json

# View message payload and error metadata headers
cat /tmp/poison_pill_sample.json | jq .
```

#### Step 3: Identify Root Cause & Apply Parser Quarantine Bypass
If the crash is caused by an unexpected vendor syslog format (e.g. malformed RFC 5424 header from a newly connected switch):
```bash
# Update ConfigMap to enable non-blocking schema quarantine mode
kubectl patch configmap vat-stream-processor-config -n vat-system --type merge -p '
{
  "data": {
    "STRICT_SCHEMA_ENFORCEMENT": "false",
    "QUARANTINE_INVALID_RECORDS": "true",
    "DLQ_ERROR_HEADER_INJECTION": "true"
  }
}
'

# Perform rolling restart of the streaming processor workers
kubectl rollout restart deployment/vat-stream-processor -n vat-system
kubectl rollout status deployment/vat-stream-processor -n vat-system --timeout=120s
```

#### Step 4: Replay Sanitized DLQ Messages into Ingestion Pipeline
Once the parser patch is deployed or records are scrubbed:
```bash
# Replay DLQ messages into raw ingestion topic with replay tag
kubectl exec -i -n vat-system vat-redpanda-0 -c redpanda -- \
  rpk topic consume vat-telemetry-dlq --offset start --num 5000 | \
  jq -c '.value | fromjson | .metadata.replayed = true' | \
  kubectl exec -i -n vat-system vat-redpanda-0 -c redpanda -- \
  rpk topic produce vat-telemetry-raw

# Verify DLQ processing metrics
kubectl exec -it -n vat-system vat-redpanda-0 -c redpanda -- rpk group describe vat-telemetry-consumer-group
```

#### Step 5: (Emergency Option) Seek Past Unrecoverable Poison Pill
If a single malformed offset is hard-locking an un-patched processor:
```bash
# Skip 1 message forward on specific partition (e.g., partition 0, offset + 1)
kubectl exec -it -n vat-system vat-redpanda-0 -c redpanda -- \
  rpk group seek vat-telemetry-consumer-group --to-offset <TARGET_OFFSET_PLUS_1> --topics vat-telemetry-raw
```

---

## Runbook 3: GPU Starvation & Out-of-Memory (Triton / Embedding Service Pod Rescheduling)

### 3.1 Trigger & Detection
* **Alerts:** `EmbeddingWorkerHighLatencyBurnRate`, `GPUMemoryExhaustionCritical`, `TritonHealthCheckFailing`
* **Symptoms:**
  * Triton Inference Server logs `CUDA out of memory` or `CUBLAS_STATUS_ALLOC_FAILED`.
  * `vat-embedding-worker` probes fail (`/health` returns 503 or hangs past 3s timeout).
  * Latency on `/embed` exceeds 2,000ms.
  * Node GPU memory allocation is pinned at 100% with no inference processing.

### 3.2 Step-by-Step Resolution Procedure

#### Step 1: Diagnose GPU Memory Allocation and Identify Stuck Node
```bash
# List worker pods and host node placement
kubectl get pods -n vat-system -l app.kubernetes.io/name=vat-embedding-worker -o wide

# Query live GPU vRAM and compute utilization via nvidia-smi across host node
kubectl exec -it -n vat-system $(kubectl get pods -n vat-system -l app.kubernetes.io/name=vat-embedding-worker -o jsonpath='{.items[0].metadata.name}') -- \
  nvidia-smi --query-gpu=index,name,memory.used,memory.free,memory.total,utilization.gpu,temperature.gpu --format=csv,nounits
```

#### Step 2: Force Immediate Pod Eviction
```bash
# Delete deadlocked worker pods with zero grace period to force immediate recreation
kubectl delete pod -n vat-system -l app.kubernetes.io/name=vat-embedding-worker --grace-period=0 --force
```

#### Step 3: Cordon Node & Reset GPU Driver State (If VRAM Remains Pinned)
If zombie CUDA contexts prevent newly scheduled pods from claiming vRAM:
```bash
# Cordon the degraded GPU host node
TARGET_NODE=$(kubectl get pods -n vat-system -l app.kubernetes.io/name=vat-embedding-worker -o jsonpath='{.items[0].spec.nodeName}')
kubectl cordon ${TARGET_NODE}

# Spawn an ephemeral privileged diagnostic pod to trigger a CUDA hardware reset
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: gpu-hardware-reset-tool
  namespace: kube-system
spec:
  nodeName: ${TARGET_NODE}
  restartPolicy: Never
  containers:
    - name: gpu-reset
      image: nvidia/cuda:12.2.0-base-ubuntu22.04
      securityContext:
        privileged: true
      command: ["sh", "-c", "nvidia-smi --gpu-reset -i 0 && echo 'GPU_RESET_SUCCESSFUL'"]
EOF

# Verify reset completion and clean up tool pod
kubectl wait --for=condition=Ready pod/gpu-hardware-reset-tool -n kube-system --timeout=30s
kubectl logs -n kube-system pod/gpu-hardware-reset-tool
kubectl delete pod gpu-hardware-reset-tool -n kube-system --ignore-not-found=true

# Uncordon host node
kubectl uncordon ${TARGET_NODE}
```

#### Step 4: Apply Dynamic Batching & Memory Allocation Limits
Prevent future vRAM OOM by throttling dynamic batch sizes and enabling memory growth limits:
```bash
# Update deployment environment variables for CUDA allocator
kubectl set env deployment/vat-embedding-worker -n vat-system \
  TRITON_MAX_BATCH_SIZE="16" \
  PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:128" \
  TF_FORCE_GPU_ALLOW_GROWTH="true"

# Verify rollout status
kubectl rollout status deployment/vat-embedding-worker -n vat-system --timeout=90s
```

#### Step 5: Validate End-to-End Inference Recovery
```bash
# Check worker health probe
kubectl exec -it -n vat-system deploy/vat-embedding-worker -- curl -s -f http://localhost:8001/health

# Perform test vector embedding inference and verify latency <= 50ms
kubectl exec -it -n vat-system deploy/vat-backend -- python -c "
import time, requests
t0 = time.time()
r = requests.post('http://vat-embedding-worker.vat-system.svc.cluster.local:8001/embed', json={'texts': ['BGP state change AS65001 down']})
latency_ms = (time.time() - t0) * 1000
print(f'Status: {r.status_code}, Dimensions: {len(r.json()[\"embeddings\"][0])}, Latency: {latency_ms:.2f}ms')
assert r.status_code == 200 and latency_ms < 500
"
```
