#!/usr/bin/env python3
"""
VAT Enterprise Platform - Cross-Platform Service Launcher
Starts Docker containers (postgres, redis, backend) and launches local frontend dev server.
"""

import subprocess
import sys
import time
import urllib.request
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


def main():
    print("=" * 65)
    print(" VAT ENTERPRISE PLATFORM // NOC SERVICE ORCHESTRATOR")
    print(" Clean Architecture • pgvector HNSW • WebSockets • Next.js NOC")
    print("=" * 65)

    # 1. Start Docker services (postgres, redis, backend)
    print("\n[1/3] Starting Docker services (postgres, redis, backend)...")
    res = subprocess.run(
        ["docker-compose", "up", "-d", "postgres", "redis", "backend"],
        cwd=str(WORKSPACE_ROOT),
    )
    if res.returncode != 0:
        print("[!] Docker Compose failed to start services. Please check Docker Desktop.")
        sys.exit(res.returncode)

    # 2. Probe Backend Health
    print("\n[2/3] Probing FastAPI backend health...")
    backend_ready = False
    for i in range(1, 11):
        time.sleep(1)
        try:
            with urllib.request.urlopen("http://localhost:8000/health", timeout=2) as response:
                if response.status == 200:
                    backend_ready = True
                    print("[✓] Backend is ONLINE! Health check passed.")
                    break
        except Exception:
            print(f"    Waiting for backend startup ({i}/10)...")

    # 3. Launch Frontend
    frontend_dir = WORKSPACE_ROOT / "frontend"
    print("\n[3/3] Launching Modern NOC Frontend Console...")
    if not (frontend_dir / "node_modules").exists():
        print("    Installing frontend npm dependencies...")
        subprocess.run(["npm", "install"], cwd=str(frontend_dir), shell=True)

    print("\n" + "=" * 65)
    print(" NOC CONSOLE READY:")
    print(" • Frontend UI:       http://localhost:3000")
    print(" • Backend REST Docs: http://localhost:8000/docs")
    print(" • Health Endpoint:   http://localhost:8000/health")
    print(" • WebSocket Stream:  ws://localhost:8000/ws/telemetry")
    print("=" * 65 + "\n")

    subprocess.run(["npm", "run", "dev"], cwd=str(frontend_dir), shell=True)


if __name__ == "__main__":
    main()
