# -*- mode: Python -*-
# Tiltfile: Enterprise DevEx Live Code Synchronization (<2.0s Hot Reload)
# Connects local engineer workspaces directly to remote EKS or vcluster sandboxes.

version_settings(constraint='>=0.30.0')

# Global Ignores to prevent unnecessary file-watching churn
watch_settings(
    ignore=[
        '**/.git',
        '**/.next',
        '**/node_modules',
        '**/__pycache__',
        '**/*.pyc',
        '**/.pytest_cache',
        '**/.mypy_cache',
        '**/*.egg-info',
        '**/dist',
        '**/build',
    ]
)

# -------------------------------------------------------------------------
# 1. Python Backend Service (FastAPI / Uvicorn Live Reload)
# -------------------------------------------------------------------------
docker_build(
    ref='vat-backend-image',
    context='./backend',
    dockerfile='./backend/Dockerfile',
    live_update=[
        # Sub-second code sync into container working directory
        sync('./backend', '/app'),
        # Re-install dependencies only if requirements.txt changes
        run(
            'pip install -r /app/requirements.txt',
            trigger=['./backend/requirements.txt'],
        ),
        # Hot-reload trigger for Python ASGI server
        run('touch /app/main.py'),
    ],
)

# -------------------------------------------------------------------------
# 2. Next.js Frontend Dashboard (Turbopack / HMR Sync)
# -------------------------------------------------------------------------
docker_build(
    ref='vat-frontend-image',
    context='./frontend',
    dockerfile='./frontend/Dockerfile',
    live_update=[
        # Sync TypeScript / JSX source files directly into container
        sync('./frontend/src', '/app/src'),
        sync('./frontend/public', '/app/public'),
        sync('./frontend/package.json', '/app/package.json'),
        # Run npm install inside container only if package dependencies change
        run(
            'npm install --prefer-offline --no-audit',
            trigger=['./frontend/package.json', './frontend/package-lock.json'],
        ),
    ],
)

# -------------------------------------------------------------------------
# 3. Virtual Core Infrastructure & Workload Bridge
# -------------------------------------------------------------------------
k8s_yaml([
    './k8s/devex/vcluster/syncer-config.yaml',
])

# Configure developer port-forwards and UI grouping
k8s_resource(
    'vat-backend',
    port_forwards=['8000:8000'],
    labels=['application', 'backend'],
)

k8s_resource(
    'vat-frontend',
    port_forwards=['3000:3000'],
    labels=['application', 'frontend'],
)

k8s_resource(
    'vat-redpanda',
    port_forwards=['9092:9092'],
    labels=['infrastructure', 'streaming'],
)

k8s_resource(
    'vat-clickhouse',
    port_forwards=['8123:8123', '9000:9000'],
    labels=['infrastructure', 'analytics'],
)
