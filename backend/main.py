"""
Vendor-Aware Troubleshooting (VAT) - Main Application Server (Phase 2)
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config.settings import get_settings
from backend.database.client import db
from backend.routes.telemetry import router as telemetry_router
from backend.routes.troubleshoot import router as troubleshoot_router

# Configure Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("vat_main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for database connection pool lifecycle."""
    logger.info("Initializing Enterprise Vendor-Aware Troubleshooting (VAT) Platform...")
    try:
        await db.connect()
    except Exception as exc:
        logger.warning("PostgreSQL connection deferred: %s", exc)

    yield

    logger.info("Shutting down VAT Platform...")
    await db.disconnect()


settings = get_settings()

app = FastAPI(
    title="Vendor-Aware AI Troubleshooter (VAT Enterprise)",
    description=(
        "Production True RAG troubleshooting & remediation platform combining live multi-vendor networking telemetry "
        "(Cisco, Juniper, VeloCloud, Arista), PostgreSQL pgvector hybrid search, and official vendor manuals."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(troubleshoot_router)
app.include_router(telemetry_router)

# Serve Console Frontend
from fastapi.responses import FileResponse, RedirectResponse

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

@app.get("/console", include_in_schema=False)
@app.get("/console/", include_in_schema=False)
async def serve_console_page():
    """Directly serve NOC console HTML page."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"detail": "Console index.html not found"}

if FRONTEND_DIR.exists():
    app.mount("/console/assets", StaticFiles(directory=str(FRONTEND_DIR)), name="console_assets")
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


class HealthResponse(BaseModel):
    status: str
    service: str
    database_connected: bool
    version: str
    timestamp: datetime


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """Service health and database connectivity probe."""
    db_ok = await db.is_connected()
    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        service="vendor-aware-troubleshooter-enterprise",
        database_connected=db_ok,
        version="2.0.0",
        timestamp=datetime.now(timezone.utc),
    )


@app.get("/", tags=["health"])
async def root() -> Dict[str, str]:
    """Root metadata endpoint."""
    return {
        "service": "Vendor-Aware AI Troubleshooter (VAT Enterprise)",
        "version": "2.0.0",
        "docs_url": "/docs",
        "health_url": "/health",
        "console_url": "/console",
        "troubleshoot_url": "/troubleshoot",
        "telemetry_url": "/telemetry/ingest",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
