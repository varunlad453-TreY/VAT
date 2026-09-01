#!/usr/bin/env python3
r"""
VAT Enterprise Platform - Tier-1 Carrier NOC Scale Architecture Implementation Plan Generator
Generates a publication-grade architectural PDF report using ReportLab.
Saved to G:\VAT Daily\Implementation Plans\03_Implementation_Plan_Tier1_Carrier_NOC_Scale_Architecture.pdf
"""

import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas

# Professional Executive Color Palette (Identical to VAT Enterprise Reference)
NAVY_DEEP = colors.HexColor("#090d16")      # Dark Obsidian
NAVY_PRIMARY = colors.HexColor("#0f172a")   # Slate 900
BLUE_ACCENT = colors.HexColor("#1d4ed8")    # Royal Blue 700
CYAN_ACCENT = colors.HexColor("#0284c7")    # Sky 600
CYAN_LIGHT = colors.HexColor("#38bdf8")     # Sky 400
EMERALD_GREEN = colors.HexColor("#059669") # Emerald 600
AMBER_WARN = colors.HexColor("#d97706")     # Amber 600
RED_CRIT = colors.HexColor("#dc2626")       # Red 600
TEXT_MAIN = colors.HexColor("#1e293b")      # Slate 800
TEXT_SECONDARY = colors.HexColor("#475569") # Slate 600
TEXT_MUTED = colors.HexColor("#64748b")     # Slate 500
BG_CARD = colors.HexColor("#f8fafc")        # Slate 50
BG_HEADER_LIGHT = colors.HexColor("#f1f5f9") # Slate 100
BORDER_LIGHT = colors.HexColor("#cbd5e1")   # Slate 300
BORDER_ACCENT = colors.HexColor("#94a3b8")  # Slate 400
RED_BG_LIGHT = colors.HexColor("#fef2f2")   # Red 50
RED_BORDER = colors.HexColor("#fca5a5")     # Red 300


class ExecutiveNumberedCanvas(canvas.Canvas):
    """Publication-quality running header and footer with dynamic total page count."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Running Top Header (pages 2+)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(NAVY_PRIMARY)
            self.drawString(45, 752, "VAT ENTERPRISE PLATFORM")
            self.setFont("Helvetica", 8)
            self.setFillColor(TEXT_MUTED)
            self.drawString(175, 752, "|  Tier-1 Carrier NOC Scale Architecture & Modernization Blueprint")
            self.drawRightString(567, 752, "CONFIDENTIAL — TIER-1 CARRIER NOC")
            self.setStrokeColor(BORDER_LIGHT)
            self.setLineWidth(0.75)
            self.line(45, 744, 567, 744)

        # Running Footer (all pages)
        self.setStrokeColor(BORDER_LIGHT)
        self.setLineWidth(0.75)
        self.line(45, 42, 567, 42)
        
        self.setFont("Helvetica", 8)
        self.setFillColor(TEXT_MUTED)
        self.drawString(45, 30, "Vendor-Aware Troubleshooting (VAT) Enterprise  •  Implementation Plan Blueprint")
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(NAVY_PRIMARY)
        self.drawRightString(567, 30, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def build_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=48,
        bottomMargin=48,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.white,
        spaceAfter=3,
    )
    subtitle_style = ParagraphStyle(
        'CoverSub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=CYAN_LIGHT,
        spaceAfter=8,
    )
    meta_title_style = ParagraphStyle(
        'MetaTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=TEXT_MUTED,
    )
    meta_val_style = ParagraphStyle(
        'MetaVal',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=NAVY_PRIMARY,
    )
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=NAVY_PRIMARY,
        spaceBefore=11,
        spaceAfter=4,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=BLUE_ACCENT,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.2,
        textColor=TEXT_MAIN,
        spaceAfter=5,
    )
    body_bold = ParagraphStyle(
        'BodyDarkBold',
        parent=body_style,
        fontName='Helvetica-Bold',
    )
    code_inline = ParagraphStyle(
        'CodeInline',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=7.5,
        leading=10,
        textColor=NAVY_PRIMARY,
    )
    card_text = ParagraphStyle(
        'CardText',
        parent=body_style,
        fontSize=8,
        leading=11.2,
        textColor=TEXT_MAIN,
    )
    crit_badge = ParagraphStyle(
        'CritBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=RED_CRIT,
    )

    story = []

    # ─────────────────────────────────────────────────────────────────────────
    # 1. EXECUTIVE TITLE BANNER (High-Impact Obsidian Hero)
    # ─────────────────────────────────────────────────────────────────────────
    banner_content = [
        [Paragraph("VAT ENTERPRISE PLATFORM", title_style)],
        [Paragraph("Tier-1 Carrier NOC Scale Architecture & Infrastructure Modernization Plan", subtitle_style)],
        [Paragraph("<font color='#94a3b8'>Decoupled 100k+ EPS Ingestion, Polyglot Persistence, Distributed Triton ML & Strangler Fig Roadmap</font>", card_text)]
    ]
    banner_table = Table(banner_content, colWidths=[522])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY_DEEP),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('LEFTPADDING', (0, 0), (-1, -1), 16),
        ('RIGHTPADDING', (0, 0), (-1, -1), 16),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#1e293b")),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 8))

    # Document Metadata Strip
    meta_table_data = [
        [
            Paragraph("DOCUMENT CLASSIFICATION", meta_title_style),
            Paragraph("ROLE / AUTHOR", meta_title_style),
            Paragraph("TARGET SCALE", meta_title_style),
            Paragraph("ARCHITECTURE STATUS", meta_title_style),
        ],
        [
            Paragraph("CONFIDENTIAL &bull; TIER-1 NOC", meta_val_style),
            Paragraph("Principal Solutions Architect", meta_val_style),
            Paragraph("100k+ EPS &bull; 50-Engineer NOC", meta_val_style),
            Paragraph("<font color='#059669'>ARCHITECTURE APPROVED</font>", meta_val_style),
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[130, 130, 142, 120])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_HEADER_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 9))

    # ─────────────────────────────────────────────────────────────────────────
    # 2. SECTION 1: THE BRUTAL REALITY CHECK
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("1. The Brutal Reality Check: Why Current Stack Dies at 100k+ EPS", h1_style))
    story.append(Paragraph(
        "Let’s stop pretending. What you have built is a neat proof-of-concept, but if you drop this into a Tier-1 NOC environment parsing <b>100k+ events per second</b> (syslogs, BGP flaps, SNMP traps), your system will immediately crater. Here is exactly how and why your current stack dies:",
        body_style
    ))

    reality_check_data = [
        [Paragraph("CHOKEPOINT / COMPONENT", meta_title_style), Paragraph("FAILURE MECHANISM & ARCHITECTURAL ROOT CAUSE", meta_title_style), Paragraph("BLAST RADIUS", meta_title_style)],
        [
            Paragraph("<b>FastAPI as Ingestion Chokepoint</b>", body_bold),
            Paragraph("FastAPI is phenomenal for control planes and REST CRUD. But piping 100k+ EPS of raw telemetry through an ASGI event loop running Python? You will hit GIL contention, CPU saturation, and garbage collection pauses that will backpressure the network and drop packets. Python is not an edge ingestion router.", card_text),
            Paragraph("<font color='#dc2626'><b>CRITICAL</b></font><br/>Packet Drops & Buffer Exhaustion", crit_badge),
        ],
        [
            Paragraph("<b>The pgvector Death Spiral</b>", body_bold),
            Paragraph("You are shoving high-velocity telemetry and vector embeddings into the same PostgreSQL 16 instance. HNSW index builds in pgvector are computationally brutal. When your index maintenance triggers during a telemetry spike, your insert latencies will spike to seconds, asyncpg connection pools will exhaust, and the database will tip over. PostgreSQL is an OLTP database, not a time-series or high-throughput vector store.", card_text),
            Paragraph("<font color='#dc2626'><b>FATAL</b></font><br/>Connection Exhaustion & DB Lockup", crit_badge),
        ],
        [
            Paragraph("<b>Synchronous ML Inference</b>", body_bold),
            Paragraph("If you are running sentence-transformers locally within the FastAPI application (or even in a standard ProcessPool), you are tying CPU-bound inference directly to your IO-bound web server. Your P99 latencies will be abysmal, and the web tier will scale linearly with embedding costs rather than request volume.", card_text),
            Paragraph("<font color='#dc2626'><b>HIGH</b></font><br/>P99 Spikes & Web Tier Thrashing", crit_badge),
        ],
        [
            Paragraph("<b>Vanilla JS in the NOC</b>", body_bold),
            Paragraph("A raw HTML/JS frontend for a real-time, high-density NOC console? Absolute suicide for a team of 50. It lacks module isolation, strict typing, and efficient DOM reconciliation. When you try to render 5,000 real-time BGP flap rows and stream updates over WebSockets, the browser thread will lock up.", card_text),
            Paragraph("<font color='#dc2626'><b>HIGH</b></font><br/>Browser Lockup & Unmaintainability", crit_badge),
        ],
        [
            Paragraph("<b>Raw .sql Script Execution</b>", body_bold),
            Paragraph("Applying raw .sql files manually or via shell scripts is amateur hour. It guarantees eventual schema drift, untracked mutations, and failed rollbacks during a sev-1 incident.", card_text),
            Paragraph("<font color='#dc2626'><b>CRITICAL</b></font><br/>Schema Drift & Sev-1 Rollback Failure", crit_badge),
        ],
    ]

    reality_table = Table(reality_check_data, colWidths=[115, 305, 102])
    reality_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('LINEBEFORE', (2, 1), (2, -1), 1, RED_BORDER),
    ]))
    for r in range(1, len(reality_check_data)):
        if r % 2 == 1:
            reality_table.setStyle(TableStyle([('BACKGROUND', (0, r), (-1, r), BG_CARD)]))
    story.append(reality_table)

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE BREAK TO PAGE 2
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────────
    # 3. SECTION 2: THE "BIG BOY" INFRASTRUCTURE BLUEPRINT
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("2. The \"Big Boy\" Infrastructure Blueprint (CQRS & Event-Driven)", h1_style))
    story.append(Paragraph(
        "We are moving to a <b>CQRS (Command Query Responsibility Segregation)</b> and <b>Event-Driven architecture</b>. We decouple ingestion from processing, and processing from serving across five enterprise tiers:",
        body_style
    ))

    # Blueprint Pillars Table
    blueprint_data = [
        [Paragraph("TIER / DOMAIN", meta_title_style), Paragraph("TECHNOLOGY STACK", meta_title_style), Paragraph("ARCHITECTURAL SPECIFICATION & SCALING PATTERN", meta_title_style)],
        [
            Paragraph("<b>A. Event Streaming & Ingestion</b><br/><font color='#1d4ed8'>The Edge</font>", card_text),
            Paragraph("<b>Vector.dev</b> (Rust)<br/><b>Redpanda</b> (C++ Cluster)", code_inline),
            Paragraph("<b>Edge Agents:</b> Deploy Vector.dev (written in Rust) at the edge as the universal receiver for syslogs, SNMP traps, and gRPC telemetry. Parses, standardizes (OpenTelemetry format), drops noise, and buffers locally.<br/>"
                      "<b>Immutable Backbone:</b> Vector forwards events to Redpanda (Kafka-compatible, C++, no JVM tuning, Thread-per-Core architecture). Handles 100k+ EPS effortlessly and uses Tiered Storage to automatically offload cold events to S3/GCS at object-storage economics.", card_text)
        ],
        [
            Paragraph("<b>B. Distributed Computing</b><br/><font color='#0284c7'>The Brain</font>", card_text),
            Paragraph("<b>Apache Flink / Benthos</b><br/><b>Triton / Ray Serve</b><br/><b>Temporal.io</b>", code_inline),
            Paragraph("<b>Telemetry Stream Processing:</b> Use Benthos or Apache Flink to consume from Redpanda, apply deterministic 4-stage remediation runbooks (if simple logic), and enrich stream metadata.<br/>"
                      "<b>Vector/Embedding Generation:</b> Extract sentence-transformers into a dedicated GPU-accelerated cluster running Triton Inference Server or Ray Serve.<br/>"
                      "<b>The RAG Pipeline:</b> When a complex anomaly is detected, a Kafka Connect sink triggers an asynchronous Celery or Temporal.io workflow. Temporal orchestrates: fetching telemetry context, invoking Triton embeddings, and querying vector/time-series stores.", card_text)
        ],
        [
            Paragraph("<b>C. Database Evolution</b><br/><font color='#059669'>Polyglot Persistence</font>", card_text),
            Paragraph("<b>ClickHouse</b> (Time-Series)<br/><b>Qdrant / Milvus</b> (Vectors)<br/><b>Postgres 16 + Alembic</b>", code_inline),
            Paragraph("<b>Hot Telemetry (Time-Series):</b> ClickHouse. Ingests 100k EPS in micro-batches from Redpanda via native ClickHouse Kafka Engine, applies high-ratio compression, and serves sub-second NOC aggregations.<br/>"
                      "<b>Vector & Knowledge Base (RAG Store):</b> Qdrant or Milvus for pure distributed HNSW vector search across millions of historical telemetry embeddings at scale.<br/>"
                      "<b>Control Plane / Relational State:</b> Keep PostgreSQL 16 strictly for user accounts, RBAC, static runbooks, and configurations. Alembic enforces strict versioned migrations.", card_text)
        ],
        [
            Paragraph("<b>D. Infrastructure as Code</b><br/><font color='#d97706'>IaC & GitOps</font>", card_text),
            Paragraph("<b>Terraform</b><br/><b>Kubernetes (EKS/GKE)</b><br/><b>ArgoCD + Helm</b>", code_inline),
            Paragraph("<b>Provisioning:</b> Terraform for all infrastructure (VPCs, EKS clusters, S3 buckets, IAM roles).<br/>"
                      "<b>Compute:</b> Kubernetes (EKS/GKE). All stateless/stateful workloads run in K8s.<br/>"
                      "<b>GitOps:</b> ArgoCD reconciling against a Helm/Kustomize manifest repository. CI builds containers and updates image tags; ArgoCD rolls out automated zero-downtime deployments.", card_text)
        ],
        [
            Paragraph("<b>E. Telemetry Observability</b><br/><font color='#64748b'>Full-Stack Tracing</font>", card_text),
            Paragraph("<b>OpenTelemetry (OTel)</b><br/><b>Prometheus / VictoriaMetrics</b><br/><b>Jaeger/Tempo & Grafana</b>", code_inline),
            Paragraph("<b>Instrumentation:</b> OpenTelemetry (OTel) SDKs in all Python and Frontend code.<br/>"
                      "<b>Metrics:</b> Prometheus (or VictoriaMetrics for scale) scraping OTel collectors.<br/>"
                      "<b>Tracing:</b> Jaeger or Tempo to trace single BGP flap from Vector.dev &rarr; Redpanda &rarr; Flink &rarr; Temporal &rarr; ClickHouse.<br/>"
                      "<b>Dashboards:</b> Unified Grafana tied to ClickHouse (network telemetry) and Prometheus (system health).", card_text)
        ],
    ]

    blueprint_table = Table(blueprint_data, colWidths=[110, 115, 297])
    blueprint_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE_ACCENT),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    for r in range(1, len(blueprint_data)):
        if r % 2 == 1:
            blueprint_table.setStyle(TableStyle([('BACKGROUND', (0, r), (-1, r), BG_CARD)]))
    story.append(blueprint_table)

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE BREAK TO PAGE 3
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────────
    # 4. SECTION 3: THE FRONTEND OVERHAUL
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("3. The Frontend Overhaul: Carrier-Grade NOC Console", h1_style))
    story.append(Paragraph(
        "To support 50 engineers and a carrier-grade NOC experience, we burn the Vanilla JS and introduce a modern, modular toolchain:",
        body_style
    ))

    frontend_data = [
        [Paragraph("FRONTEND PILLAR", meta_title_style), Paragraph("TECHNOLOGY", meta_title_style), Paragraph("ENGINEERING JUSTIFICATION & ARCHITECTURAL IMPLEMENTATION", meta_title_style)],
        [
            Paragraph("<b>Core Framework</b>", body_bold),
            Paragraph("<b>Next.js (App Router)</b><br/>+ TypeScript & Turborepo", code_inline),
            Paragraph("Strict typing is mandatory. Monorepo manager (Turborepo) allows separate module ownership (<code>packages/ui</code>, <code>apps/noc-dashboard</code>, <code>apps/admin-panel</code>) across 50 engineers.", card_text)
        ],
        [
            Paragraph("<b>Real-time Streaming</b>", body_bold),
            Paragraph("<b>gRPC-Web</b> or<br/><b>Centrifugo Pub/Sub</b>", code_inline),
            Paragraph("Replaces standard raw WebSockets with high-scale binary or structured pub/sub streaming to browser clients with connection multiplexing and tokenized channel auth.", card_text)
        ],
        [
            Paragraph("<b>State & Data Fetching</b>", body_bold),
            Paragraph("<b>TanStack Query</b><br/>+ <b>Zustand</b>", code_inline),
            Paragraph("React Query (TanStack Query) for server state caching (Runbooks, user profiles) and Zustand for fast, transient UI state (sidebars, live filter toggles).", card_text)
        ],
        [
            Paragraph("<b>High-Density Rendering</b>", body_bold),
            Paragraph("<b>TanStack Virtual</b><br/>(Virtualized Lists)", code_inline),
            Paragraph("Virtualized viewport rendering for high-density 10,000+ row BGP flap and syslog event streams, eliminating DOM bloat and preventing browser thread lockups.", card_text)
        ],
        [
            Paragraph("<b>Design System & UI</b>", body_bold),
            Paragraph("<b>Tailwind CSS</b><br/>+ <b>shadcn/ui (Radix)</b>", code_inline),
            Paragraph("Accessible, un-opinionated Obsidian Slate design tokens. Eliminates CSS specificity wars across 50 engineers with headless Radix UI primitives.", card_text)
        ],
    ]

    frontend_table = Table(frontend_data, colWidths=[105, 120, 297])
    frontend_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    for r in range(1, len(frontend_data)):
        if r % 2 == 1:
            frontend_table.setStyle(TableStyle([('BACKGROUND', (0, r), (-1, r), BG_CARD)]))
    story.append(frontend_table)
    story.append(Spacer(1, 8))

    # ─────────────────────────────────────────────────────────────────────────
    # 5. SECTION 4: THE EXECUTION ROADMAP (STRANGLER FIG PATTERN)
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("4. The Execution Roadmap: Strangler Fig Pattern", h1_style))
    story.append(Paragraph(
        "We do not rewrite from scratch; we strangle the legacy system while keeping the lights on via four phased iterations:",
        body_style
    ))

    roadmap_data = [
        [
            Paragraph("<b>PHASE 1: Stop Bleeding & Stabilize</b><br/><font color='#1d4ed8'>Weeks 1–4</font><br/>"
                      "&bull; <b>Database:</b> Introduce Alembic; baseline current PostgreSQL database. Eliminate raw .sql scripts.<br/>"
                      "&bull; <b>Compute Isolation:</b> Strip sentence-transformers out of FastAPI request cycle into Celery/Redis queue or standalone GPU service.<br/>"
                      "&bull; <b>Frontend Prep:</b> Scaffold Turborepo monorepo and Next.js shell.", card_text),
            Paragraph("<b>PHASE 2: Ingestion Decoupling</b><br/><font color='#0284c7'>Months 2–3</font><br/>"
                      "&bull; <b>Deploy Redpanda & Vector.dev:</b> Reroute network devices (syslog/traps) to Vector.dev &rarr; Redpanda.<br/>"
                      "&bull; <b>Strangler Fig API:</b> Modify FastAPI to consume events from Redpanda background workers instead of exposing raw ingestion POST endpoints.", card_text),
        ],
        [
            Paragraph("<b>PHASE 3: Polyglot Persistence & RAG</b><br/><font color='#059669'>Months 4–5</font><br/>"
                      "&bull; <b>ClickHouse:</b> Stand up ClickHouse; sink Redpanda telemetry directly to ClickHouse via Kafka Engine.<br/>"
                      "&bull; <b>API Refactor:</b> Point FastAPI dashboard reads to ClickHouse for time-series analytics.<br/>"
                      "&bull; <b>Vector Migration:</b> Move high-velocity embeddings to Qdrant. Keep PostgreSQL strictly for relational state.", card_text),
            Paragraph("<b>PHASE 4: Frontend Cut-Over</b><br/><font color='#d97706'>Months 3–6</font><br/>"
                      "&bull; <b>Strangler UI:</b> Next.js acts as proxy. Build RAG & Vector search natively in Next.js; embed legacy pages via iframe.<br/>"
                      "&bull; <b>Virtualization:</b> Implement TanStack Virtual & gRPC-Web for real-time NOC feeds.<br/>"
                      "&bull; <b>Decommission:</b> Delete last Vanilla JS file and retire static file server.", card_text),
        ]
    ]

    roadmap_table = Table(roadmap_data, colWidths=[256, 266])
    roadmap_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_HEADER_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('LINELEFT', (0, 0), (0, 0), 3, BLUE_ACCENT),
        ('LINELEFT', (1, 0), (1, 0), 3, CYAN_ACCENT),
        ('LINELEFT', (0, 1), (0, 1), 3, EMERALD_GREEN),
        ('LINELEFT', (1, 1), (1, 1), 3, AMBER_WARN),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(roadmap_table)
    story.append(Spacer(1, 8))

    # Architecture Sign-off Banner
    signoff_data = [[
        Paragraph("<b>Engineering Architectural Decision Record (ADR) Summary:</b><br/>"
                  "&bull; <b>Ingestion Throughput:</b> Scaled from ~500 EPS (FastAPI ASGI chokepoint) to <b>100,000+ EPS</b> via Vector.dev & Redpanda.<br/>"
                  "&bull; <b>Persistence Strategy:</b> Decoupled OLTP (PostgreSQL 16) from Time-Series (ClickHouse) and Vector RAG (Qdrant/Milvus).<br/>"
                  "&bull; <b>Frontend Scalability:</b> Replaced unmaintainable Vanilla JS with typed Next.js App Router, TanStack Virtual, and gRPC-Web.", card_text)
    ]]
    signoff_table = Table(signoff_data, colWidths=[522])
    signoff_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_CARD),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#86efac")),
        ('LINELEFT', (0, 0), (0, 0), 4, EMERALD_GREEN),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(signoff_table)

    # Build Document
    doc.build(story, canvasmaker=ExecutiveNumberedCanvas)
    print(f"Implementation Plan PDF successfully generated at: {output_path}")


if __name__ == "__main__":
    target_dir = Path(r"G:\VAT Daily\Implementation Plans")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    primary_pdf = target_dir / "03_Implementation_Plan_Tier1_Carrier_NOC_Scale_Architecture.pdf"
    build_pdf(str(primary_pdf))

    # Also save with alternative intuitive names
    alt_pdf = target_dir / "Tier1_NOC_Architecture_Blueprint.pdf"
    build_pdf(str(alt_pdf))
