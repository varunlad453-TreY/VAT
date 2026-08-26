"""
Presentation Layer: WebSocket Streaming Handlers
Real-time streaming of telemetry parsing, live incident feeds, and RAG synthesis progress.
"""

import json
import logging
from typing import Any, Dict, List, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.application.dtos.troubleshoot_dto import TroubleshootRequestDTO
from backend.domain.entities.citation import VendorDocCitation
from backend.presentation.dependencies import (
    get_ai_synthesizer,
    get_audit_repository,
    get_cache_service,
    get_telemetry_parser,
    get_vector_repository,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websockets"])


class ConnectionManager:
    """Manages active WebSocket client connections and multi-channel broadcast dispatch."""

    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("WebSocket client connected. Total active: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Unregister closed WebSocket connection."""
        self.active_connections.discard(websocket)
        logger.info("WebSocket client disconnected. Total active: %d", len(self.active_connections))

    async def send_json(self, message: Dict[str, Any], websocket: WebSocket) -> None:
        """Send direct JSON message to a single connected client."""
        try:
            await websocket.send_json(message)
        except Exception as exc:
            logger.debug("Failed to send WebSocket message: %s", exc)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast JSON payload to all connected clients."""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as exc:
                logger.debug("Broadcast error to client, scheduling removal: %s", exc)
                disconnected.add(connection)

        for dead_conn in disconnected:
            self.active_connections.discard(dead_conn)


ws_manager = ConnectionManager()


@router.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for live telemetry streaming.
    Clients receive real-time multi-vendor parsed logs and incident alerts.
    """
    await ws_manager.connect(websocket)
    telemetry_parser = get_telemetry_parser()

    try:
        # Send initial connection handshake
        await ws_manager.send_json(
            {
                "type": "connection_established",
                "message": "Connected to VAT Enterprise Real-Time Telemetry Stream",
                "active_connections": len(ws_manager.active_connections),
            },
            websocket,
        )

        while True:
            raw_data = await websocket.receive_text()
            try:
                data = json.loads(raw_data)
                raw_log = data.get("log", raw_data)
                device_hint = data.get("device_hint")
            except Exception:
                raw_log = raw_data
                device_hint = None

            # Parse received telemetry live
            parsed = telemetry_parser.parse_log(raw_log, device_hint=device_hint)
            event_payload = {
                "type": "telemetry_event",
                "parsed": parsed.model_dump(),
            }

            # Echo to sender and broadcast to other connected NOC dashboards
            await ws_manager.send_json(event_payload, websocket)
            await ws_manager.broadcast({
                "type": "telemetry_broadcast",
                "event": parsed.model_dump(),
            })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as exc:
        logger.warning("WebSocket telemetry stream exception: %s", exc)
        ws_manager.disconnect(websocket)


@router.websocket("/ws/troubleshoot")
async def websocket_troubleshoot_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for live step-by-step RAG runbook synthesis progress.
    Streams diagnostic phases: parsing -> hybrid search -> synthesis -> audit recording.
    """
    await ws_manager.connect(websocket)
    telemetry_parser = get_telemetry_parser()
    vector_repo = get_vector_repository()
    ai_synthesizer = get_ai_synthesizer()
    audit_repo = get_audit_repository()

    try:
        await ws_manager.send_json(
            {
                "type": "connection_established",
                "message": "Connected to VAT Real-Time Synthesis Stream",
            },
            websocket,
        )

        while True:
            raw_data = await websocket.receive_text()
            try:
                data = json.loads(raw_data)
                raw_logs = data.get("raw_logs", raw_data)
                device_id = data.get("device_id")
                vendor = data.get("vendor")
                protocol = data.get("protocol")
            except Exception:
                raw_logs = raw_data
                device_id = None
                vendor = None
                protocol = None

            if not raw_logs or not raw_logs.strip():
                await ws_manager.send_json({"type": "error", "message": "raw_logs cannot be empty"}, websocket)
                continue

            # Stage 1: Parse telemetry
            await ws_manager.send_json({"type": "progress", "stage": "parsing", "message": "Parsing multi-vendor telemetry tokens..."}, websocket)
            parsed = telemetry_parser.parse_log(raw_logs, device_hint=device_id)

            effective_vendor = vendor or parsed.vendor
            effective_protocol = protocol or parsed.protocol
            effective_device = device_id or parsed.device_id

            await ws_manager.send_json({
                "type": "progress",
                "stage": "parsed",
                "vendor": effective_vendor,
                "protocol": effective_protocol,
                "severity": parsed.severity,
            }, websocket)

            # Stage 2: Hybrid RRF Search
            await ws_manager.send_json({"type": "progress", "stage": "retrieval", "message": f"Querying pgvector HNSW + BM25 RRF for {effective_vendor.upper()} TAC docs..."}, websocket)
            docs = await vector_repo.find_relevant_docs(
                query_text=raw_logs,
                limit=3,
                vendor=effective_vendor,
                protocol=effective_protocol,
            )
            citations = [
                VendorDocCitation(
                    source_url=d["source_url"],
                    title=d["title"],
                    vendor=d.get("vendor", effective_vendor),
                    similarity_score=round(float(d.get("similarity", 0.88)), 3),
                    excerpt=d["chunk_text"][:280] + "...",
                )
                for d in docs
            ]

            await ws_manager.send_json({
                "type": "progress",
                "stage": "retrieved_citations",
                "citations_count": len(citations),
                "citations": [c.model_dump() for c in citations],
            }, websocket)

            # Stage 3: Synthesis
            await ws_manager.send_json({"type": "progress", "stage": "synthesizing", "message": "Synthesizing 4-stage operational remediation runbook..."}, websocket)
            req_dto = TroubleshootRequestDTO(
                device_id=effective_device,
                vendor=effective_vendor,
                protocol=effective_protocol,
                raw_logs=raw_logs,
            )
            runbook = await ai_synthesizer.synthesize_runbook(
                request=req_dto,
                parsed_telemetry=parsed,
                citations=citations,
                relevant_docs=docs,
            )

            # Stage 4: Completed
            await ws_manager.send_json({
                "type": "runbook_completed",
                "runbook": runbook.model_dump(mode="json"),
            }, websocket)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as exc:
        logger.warning("WebSocket troubleshooting stream exception: %s", exc)
        ws_manager.disconnect(websocket)
