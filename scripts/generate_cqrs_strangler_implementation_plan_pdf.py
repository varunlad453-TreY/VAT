#!/usr/bin/env python3
r"""
VAT Enterprise Platform - CQRS & Event-Driven Architecture Implementation Plan PDF Generator
Generates a publication-grade architectural PDF report using ReportLab.
Saved to G:\VAT Daily\Implementation Plans\04_Implementation_Plan_CQRS_Event_Driven_Strangler_Fig.pdf
and G:\VAT Daily\Implementation Plans\03_Implementation_Plan_Tier1_Carrier_NOC_Scale_Architecture.pdf
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

# Professional Executive Color Palette (High-End Corporate / NOC Grade)
NAVY_DEEP = colors.HexColor("#090d16")      # Dark Obsidian
NAVY_PRIMARY = colors.HexColor("#0f172a")   # Slate 900
BLUE_ACCENT = colors.HexColor("#1d4ed8")    # Royal Blue 700
CYAN_ACCENT = colors.HexColor("#0284c7")    # Sky 600
CYAN_LIGHT = colors.HexColor("#38bdf8")     # Sky 400
EMERALD_GREEN = colors.HexColor("#059669") # Emerald 600
AMBER_WARN = colors.HexColor("#d97706")     # Amber 600
RED_CRIT = colors.HexColor("#dc2626")       # Red 600
PURPLE_ACCENT = colors.HexColor("#7c3aed")  # Violet 600
TEXT_MAIN = colors.HexColor("#1e293b")      # Slate 800
TEXT_SECONDARY = colors.HexColor("#475569") # Slate 600
TEXT_MUTED = colors.HexColor("#64748b")     # Slate 500
BG_CARD = colors.HexColor("#f8fafc")        # Slate 50
BG_HEADER_LIGHT = colors.HexColor("#f1f5f9") # Slate 100
BORDER_LIGHT = colors.HexColor("#cbd5e1")   # Slate 300
BORDER_ACCENT = colors.HexColor("#94a3b8")  # Slate 400
RED_BG_LIGHT = colors.HexColor("#fef2f2")   # Red 50
RED_BORDER = colors.HexColor("#fca5a5")     # Red 300
GREEN_BG_LIGHT = colors.HexColor("#f0fdf4") # Green 50
GREEN_BORDER = colors.HexColor("#86efac")   # Green 300
BLUE_BG_LIGHT = colors.HexColor("#eff6ff")  # Blue 50
BLUE_BORDER = colors.HexColor("#bfdbfe")   # Blue 200


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
            self.drawString(175, 752, "|  CQRS, Event-Driven Ingestion & Strangler Fig Architecture Blueprint")
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
        self.drawString(45, 30, "Vendor-Aware Troubleshooting (VAT) Enterprise  •  Architecture Implementation Blueprint")
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
        fontSize=18.5,
        leading=22.5,
        textColor=colors.white,
        spaceAfter=3,
    )
    subtitle_style = ParagraphStyle(
        'CoverSub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.8,
        leading=13.5,
        textColor=CYAN_LIGHT,
        spaceAfter=6,
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
        fontSize=11.2,
        leading=14.2,
        textColor=NAVY_PRIMARY,
        spaceBefore=8,
        spaceAfter=3.5,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=BLUE_ACCENT,
        spaceBefore=4.5,
        spaceAfter=2,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.1,
        leading=11.5,
        textColor=TEXT_MAIN,
        spaceAfter=4,
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
        fontSize=7.2,
        leading=9.5,
        textColor=NAVY_PRIMARY,
    )
    card_text = ParagraphStyle(
        'CardText',
        parent=body_style,
        fontSize=7.8,
        leading=10.8,
        textColor=TEXT_MAIN,
    )
    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.2,
        leading=9.5,
        textColor=BLUE_ACCENT,
    )

    story = []

    # ─────────────────────────────────────────────────────────────────────────
    # 1. EXECUTIVE TITLE BANNER (Obsidian Hero)
    # ─────────────────────────────────────────────────────────────────────────
    banner_content = [
        [Paragraph("VAT ENTERPRISE PLATFORM", title_style)],
        [Paragraph("CQRS, Event-Driven Telemetry Ingestion & Strangler Fig Architecture Specification", subtitle_style)],
        [Paragraph("<font color='#94a3b8'>Edge Vector.dev Routing, Redpanda Tiered Streaming, Polyglot Persistence, Triton ML & Turborepo Console</font>", card_text)]
    ]
    banner_table = Table(banner_content, colWidths=[522])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY_DEEP),
        ('TOPPADDING', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 11),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#1e293b")),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 5))

    # Metadata Strip
    meta_table_data = [
        [
            Paragraph("DOCUMENT CLASSIFICATION", meta_title_style),
            Paragraph("ARCHITECTURE MODEL", meta_title_style),
            Paragraph("INGESTION SLA TARGET", meta_title_style),
            Paragraph("MIGRATION STRATEGY", meta_title_style),
        ],
        [
            Paragraph("CONFIDENTIAL &bull; TIER-1 NOC", meta_val_style),
            Paragraph("CQRS &bull; Event-Driven", meta_val_style),
            Paragraph("100,000+ EPS &bull; 99.999% Uptime", meta_val_style),
            Paragraph("<font color='#0284c7'>STRANGLER FIG PATTERN</font>", meta_val_style),
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[130, 130, 142, 120])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_HEADER_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6))

    # ─────────────────────────────────────────────────────────────────────────
    # 2. SECTION 1: ARCHITECTURAL MANDATE & CORE DECOUPLING
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("1. Core Mandate: CQRS & Event-Driven Decomposition", h1_style))
    story.append(Paragraph(
        "We are moving to an <b>Event-Driven, CQRS (Command Query Responsibility Segregation) architecture</b>. We strictly decouple ingestion from processing, and processing from serving across five enterprise tiers:",
        body_style
    ))

    tier_ab_data = [
        [Paragraph("TIER / SUB-SYSTEM", meta_title_style), Paragraph("TECHNOLOGY STACK", meta_title_style), Paragraph("ARCHITECTURAL SPECIFICATION & OPERATIONAL BEHAVIOR", meta_title_style)],
        [
            Paragraph("<b>A. Event Streaming & Ingestion</b><br/><font color='#1d4ed8'>The Edge</font>", body_bold),
            Paragraph("<b>Vector.dev</b> (Rust)<br/><b>Redpanda</b> (C++ Cluster)", code_inline),
            Paragraph("<b>You do not send raw syslogs to a REST API.</b><br/>"
                      "&bull; <b>Edge Agents:</b> Deploy Vector.dev (written in Rust) at the edge (on the routers/switches' collector nodes). It acts as the universal receiver. It parses, standardizes to JSON, drops noise, and buffers locally.<br/>"
                      "&bull; <b>The Immutable Backbone:</b> Vector forwards events to Redpanda (Kafka-compatible, C++, Thread-per-Core). Redpanda handles 100k+ EPS effortlessly and uses Tiered Storage to push cold events to S3/GCS, giving infinite retention at object-storage prices.", card_text)
        ],
        [
            Paragraph("<b>B. Distributed Computing</b><br/><font color='#0284c7'>The Brain</font>", body_bold),
            Paragraph("<b>Apache Flink / Benthos</b><br/><b>Triton / Ray Serve</b><br/><b>Temporal.io</b>", code_inline),
            Paragraph("&bull; <b>Telemetry Stream Processing:</b> Use Benthos or Apache Flink to consume from Redpanda. Flink will handle windowing, deduplication of flap events, and applying simple rule-based remediation.<br/>"
                      "&bull; <b>Embedding Generation & RAG:</b> Extract sentence-transformers out of FastAPI completely. Put it in a dedicated GPU-accelerated cluster running Triton Inference Server or Ray Serve.<br/>"
                      "&bull; <b>Orchestration:</b> When complex synthesis is needed, use Temporal.io. Temporal handles the workflow: fetching context, calling Triton for the embedding, and querying the vector DB. It guarantees state; if a worker dies mid-remediation, Temporal picks up exactly where it left off.", card_text)
        ],
    ]

    tier_ab_table = Table(tier_ab_data, colWidths=[110, 115, 297])
    tier_ab_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    for r in range(1, len(tier_ab_data)):
        if r % 2 == 1:
            tier_ab_table.setStyle(TableStyle([('BACKGROUND', (0, r), (-1, r), BG_CARD)]))
    story.append(tier_ab_table)

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE BREAK TO PAGE 2
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────────
    # 3. SECTION 2: POLYGLOT PERSISTENCE, IAC & OBSERVABILITY
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("2. Polyglot Persistence, IaC, GitOps & Full-Stack Observability", h1_style))
    story.append(Paragraph(
        "<b>Stop putting everything in Postgres.</b> We partition storage engine workloads according to access patterns, retention models, and query latencies:",
        body_style
    ))

    tier_cde_data = [
        [Paragraph("TIER / CAPABILITY", meta_title_style), Paragraph("TECHNOLOGY STACK", meta_title_style), Paragraph("TECHNICAL SPECIFICATION & ENTERPRISE INTEGRATION", meta_title_style)],
        [
            Paragraph("<b>C. Polyglot Persistence</b><br/><font color='#059669'>Database Evolution</font>", body_bold),
            Paragraph("<b>ClickHouse</b> (Hot TS)<br/><b>Qdrant / Milvus</b> (RAG)<br/><b>PostgreSQL 16</b> (Control)", code_inline),
            Paragraph("&bull; <b>Hot Telemetry (Time-Series):</b> ClickHouse. It will ingest 100k EPS in batches from Redpanda, compress it by 90%, and serve sub-second aggregations for the NOC dashboards.<br/>"
                      "&bull; <b>Vector & Knowledge Base (The RAG Store):</b> Use Qdrant or Milvus for distributed vector search. They are purpose-built for high-throughput vector queries.<br/>"
                      "&bull; <b>Control Plane:</b> Keep PostgreSQL 16. Use it strictly for user accounts, RBAC, static runbook definitions, and the <code>troubleshooting_audit_ledger</code>. Manage it strictly via Alembic migrations.", card_text)
        ],
        [
            Paragraph("<b>D. Infrastructure as Code</b><br/><font color='#d97706'>IaC & GitOps</font>", body_bold),
            Paragraph("<b>Terraform</b><br/><b>Kubernetes (EKS/GKE)</b><br/><b>ArgoCD + Helm</b>", code_inline),
            Paragraph("&bull; <b>Provisioning:</b> Terraform for everything (VPCs, EKS/GKE clusters, S3 buckets, IAM).<br/>"
                      "&bull; <b>Compute:</b> Kubernetes (EKS/GKE). Everything runs in K8s.<br/>"
                      "&bull; <b>GitOps:</b> ArgoCD reconciling against a Helm/Kustomize repository. Zero manual <code>kubectl apply</code>. You commit code, CI builds the container, updates the image tag, and ArgoCD rolls it out with zero downtime.", card_text)
        ],
        [
            Paragraph("<b>E. Observability</b><br/><font color='#7c3aed'>Distributed Tracing</font>", body_bold),
            Paragraph("<b>OpenTelemetry (OTel)</b><br/><b>Prometheus / Tempo</b><br/><b>Grafana Dashboards</b>", code_inline),
            Paragraph("&bull; <b>Instrumentation:</b> OpenTelemetry (OTel) SDKs in all Python and Frontend code.<br/>"
                      "&bull; <b>Metrics & Tracing:</b> Prometheus (metrics) and Jaeger/Tempo (distributed tracing). You must be able to trace a single BGP flap from Vector.dev &rarr; Redpanda &rarr; Flink &rarr; Temporal &rarr; ClickHouse.<br/>"
                      "&bull; <b>Dashboards:</b> Unified Grafana.", card_text)
        ],
    ]

    tier_cde_table = Table(tier_cde_data, colWidths=[110, 115, 297])
    tier_cde_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE_ACCENT),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    for r in range(1, len(tier_cde_data)):
        if r % 2 == 1:
            tier_cde_table.setStyle(TableStyle([('BACKGROUND', (0, r), (-1, r), BG_CARD)]))
    story.append(tier_cde_table)
    story.append(Spacer(1, 6))

    # ─────────────────────────────────────────────────────────────────────────
    # 4. SECTION 3: THE FRONTEND OVERHAUL
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("3. The Frontend Overhaul: High-Performance NOC Console", h1_style))
    story.append(Paragraph(
        "To support a carrier-grade NOC experience and a 50-engineer team, <b>we burn the Vanilla JS</b> in favor of a type-safe, modular frontend stack:",
        body_style
    ))

    frontend_pillars_data = [
        [Paragraph("PILLAR", meta_title_style), Paragraph("TECHNOLOGY", meta_title_style), Paragraph("ENGINEERING JUSTIFICATION & ARCHITECTURAL PATTERN", meta_title_style)],
        [
            Paragraph("<b>Core Framework</b>", body_bold),
            Paragraph("<b>Next.js (App Router)</b><br/>+ TypeScript", code_inline),
            Paragraph("Strict typing is mandatory to match the backend Pydantic models.", card_text)
        ],
        [
            Paragraph("<b>Monorepo Architecture</b>", body_bold),
            Paragraph("<b>Turborepo</b>", code_inline),
            Paragraph("Split the codebase: <code>packages/ui</code>, <code>apps/noc-console</code>, <code>apps/admin-panel</code>.", card_text)
        ],
        [
            Paragraph("<b>High-Perf Rendering</b>", body_bold),
            Paragraph("<b>TanStack Virtual</b><br/>(Virtualized Lists)", code_inline),
            Paragraph("For the high-density event log, use TanStack Virtual to render only what's in the DOM viewport. The browser handles 100 elements, not 100,000.", card_text)
        ],
        [
            Paragraph("<b>Real-time Telemetry</b>", body_bold),
            Paragraph("<b>gRPC-Web / Centrifugo</b>", code_inline),
            Paragraph("For massive scale pub/sub to the browser with connection multiplexing.", card_text)
        ],
        [
            Paragraph("<b>State Management</b>", body_bold),
            Paragraph("<b>TanStack Query + Zustand</b>", code_inline),
            Paragraph("React Query (TanStack Query) for server state (Runbooks) and Zustand for transient UI state.", card_text)
        ],
        [
            Paragraph("<b>Design System & Styling</b>", body_bold),
            Paragraph("<b>Tailwind CSS + shadcn/ui</b>", code_inline),
            Paragraph("Gives a beautiful, accessible design system that prevents CSS specificity wars.", card_text)
        ],
    ]

    fe_table = Table(frontend_pillars_data, colWidths=[105, 120, 297])
    fe_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    for r in range(1, len(frontend_pillars_data)):
        if r % 2 == 1:
            fe_table.setStyle(TableStyle([('BACKGROUND', (0, r), (-1, r), BG_CARD)]))
    story.append(fe_table)

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE BREAK TO PAGE 3
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────────
    # 5. SECTION 4: THE EXECUTION ROADMAP (STRANGLER FIG PATTERN)
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("4. The Execution Roadmap: Strangler Fig Pattern", h1_style))
    story.append(Paragraph(
        "<b>We do not rewrite from scratch and pray.</b> We strangle the legacy system while keeping the lights on across four disciplined phases:",
        body_style
    ))

    roadmap_detailed = [
        [
            Paragraph("<b>PHASE 1: Stop the Bleeding &amp; Stabilize</b><br/><font color='#1d4ed8'><b>Timeline: Weeks 1&ndash;4 &bull; [COMPLETE]</b></font><br/>"
                      "&bull; <b>Database:</b> Introduce Alembic. Baseline the current PostgreSQL database. Delete the raw .sql files.<br/>"
                      "&bull; <b>Compute Isolation:</b> Strip sentence-transformers out of the FastAPI request cycle. Put it behind a simple Celery/Redis queue or a standalone FastAPI microservice on a GPU node.<br/>"
                      "&bull; <b>Frontend Prep:</b> Scaffold the Turborepo and Next.js shell alongside the existing code.", card_text),
            Paragraph("<b>PHASE 2: Ingestion Decoupling</b><br/><font color='#0284c7'><b>Timeline: Months 2&ndash;3 &bull; [UPCOMING]</b></font><br/>"
                      "&bull; <b>Deploy Redpanda &amp; Vector.dev:</b> Reroute all network devices to send syslogs to Vector.dev, which forwards to Redpanda.<br/>"
                      "&bull; <b>Strangler Fig the API:</b> Modify the existing FastAPI app to consume events from Redpanda via a background consumer, deprecating the <code>/telemetry/ingest</code> HTTP endpoints.", card_text),
        ],
        [
            Paragraph("<b>PHASE 3: Polyglot Persistence &amp; RAG Separation</b><br/><font color='#059669'><b>Timeline: Months 4&ndash;5</b></font><br/>"
                      "&bull; <b>ClickHouse:</b> Stand up ClickHouse. Configure Redpanda to sink telemetry directly to ClickHouse.<br/>"
                      "&bull; <b>API Refactor:</b> Point the FastAPI \"Dashboard\" read endpoints to query ClickHouse for time-series data instead of PostgreSQL.<br/>"
                      "&bull; <b>Vector Migration:</b> Move high-velocity embeddings to Qdrant. Keep PostgreSQL strictly for the relational control plane.", card_text),
            Paragraph("<b>PHASE 4: Frontend Cut-over</b><br/><font color='#d97706'><b>Timeline: Months 5&ndash;6</b></font><br/>"
                      "&bull; <b>Implement Strangler Fig on UI:</b> The Next.js app acts as a proxy.<br/>"
                      "&bull; <b>Incremental Migration:</b> Legacy Vanilla JS pages are embedded via &lt;iframe&gt; or incrementally rewritten route-by-route.<br/>"
                      "&bull; <b>NOC Feeds:</b> Implement TanStack Virtual and gRPC-Web for real-time feed.<br/>"
                      "&bull; <b>Decommission:</b> Once the last Vanilla JS file is deleted, decommission the old static file server.", card_text),
        ]
    ]

    roadmap_table = Table(roadmap_detailed, colWidths=[256, 266])
    roadmap_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_HEADER_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('LINELEFT', (0, 0), (0, 0), 3.5, BLUE_ACCENT),
        ('LINELEFT', (1, 0), (1, 0), 3.5, CYAN_ACCENT),
        ('LINELEFT', (0, 1), (0, 1), 3.5, EMERALD_GREEN),
        ('LINELEFT', (1, 1), (1, 1), 3.5, AMBER_WARN),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(roadmap_table)
    story.append(Spacer(1, 6))

    # Phase 1 Completion Status Callout
    status_box = [
        [
            Paragraph("<b>PHASE 1 IMPLEMENTATION STATUS: VERIFIED & COMMITTED</b>", ParagraphStyle('HdrPass', parent=body_bold, textColor=EMERALD_GREEN)),
        ],
        [
            Paragraph(
                "&bull; <b>Alembic Asyncpg Baseline:</b> Configured and verified with idempotent HNSW + BM25 indexes ([Commit 0bf57f3]).<br/>"
                "&bull; <b>Compute Isolation Worker:</b> Dedicated microservice (port 8002) with K8s HPA/PDB and Resilient Tenacity Client active.<br/>"
                "&bull; <b>Production Data Integrity Audit:</b> Completed with <b>[CLEAN]</b> verdict across all operational entities.<br/>"
                "&bull; <b>Frontend Monorepo:</b> Turborepo initialized with Next.js 14 App Router Strangler Fig reverse proxy gateway.<br/>"
                "&bull; <b>Automated Test Suite:</b> 63/63 Pytest Unit & Integration Tests Passed (100% Green).",
                card_text
            )
        ]
    ]
    status_table = Table(status_box, colWidths=[522])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), GREEN_BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, GREEN_BORDER),
        ('LINELEFT', (0, 0), (0, 0), 4, EMERALD_GREEN),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(status_table)

    # Build Document
    doc.build(story, canvasmaker=ExecutiveNumberedCanvas)
    print(f"[SUCCESS] Implementation Plan PDF generated at: {output_path}")


if __name__ == "__main__":
    target_dir = Path(r"G:\VAT Daily\Implementation Plans")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    primary_pdf = target_dir / "03_Implementation_Plan_Tier1_Carrier_NOC_Scale_Architecture.pdf"
    build_pdf(str(primary_pdf))

    detailed_pdf = target_dir / "04_Implementation_Plan_CQRS_Event_Driven_Strangler_Fig.pdf"
    build_pdf(str(detailed_pdf))
