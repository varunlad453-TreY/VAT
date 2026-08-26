"""
Vendor-Aware Troubleshooting (VAT) - Main Application Server (Clean Architecture)
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.database.client import db
from backend.presentation.api.health_router import router as health_router
from backend.presentation.api.telemetry_router import router as telemetry_router
from backend.presentation.api.troubleshoot_router import router as troubleshoot_router
from backend.presentation.websockets.telemetry_ws import router as ws_router
from config.settings import get_settings

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

# Register Presentation Routers (REST & WebSockets)
app.include_router(troubleshoot_router)
app.include_router(telemetry_router)
app.include_router(health_router)
app.include_router(ws_router)

# Serve Console Frontend
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
