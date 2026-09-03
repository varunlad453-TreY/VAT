#!/usr/bin/env python3
"""
==============================================================================
Executive PDF Generator: Day 2 Operations Implementation Plan
Theme: VAT Enterprise Carrier-Grade CQRS & Event-Driven Architecture
Target: G:\VAT Daily\Implementation Plans\05_Implementation_Plan_Day2_Operations_ClickHouse_Redpanda_Chaos_GitOps.pdf
==============================================================================
"""

import os
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Primary Accent Bar on top
        self.setFillColor(colors.HexColor("#0B132B"))
        self.rect(0, letter[1] - 8, letter[0], 8, fill=True, stroke=False)
        self.setFillColor(colors.HexColor("#0284C7"))
        self.rect(0, letter[1] - 8, letter[0] * 0.35, 8, fill=True, stroke=False)

        # Header Text (Pages > 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(54, letter[1] - 28, "VAT ENTERPRISE: DAY 2 OPERATIONS IMPLEMENTATION PLAN")
            self.setFont("Helvetica", 8)
            self.drawRightString(letter[0] - 54, letter[1] - 28, "CARRIER-GRADE CQRS & GITOPS")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.75)
            self.line(54, letter[1] - 34, letter[0] - 54, letter[1] - 34)

        # Footer
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(54, 45, letter[0] - 54, 45)

        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#0B132B"))
        self.drawString(54, 32, "CONFIDENTIAL & PROPRIETARY")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(200, 32, "•  Tier-1 Carrier NOC Architecture  •  Zero-Downtime Cut-Over")

        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 54, 32, page_str)
        self.restoreState()


def generate_pdf():
    output_dir = Path(r"G:\VAT Daily\Implementation Plans")
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / "05_Implementation_Plan_Day2_Operations_ClickHouse_Redpanda_Chaos_GitOps.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=50,
        bottomMargin=55,
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    C_PRIMARY = colors.HexColor("#0B132B")
    C_SECONDARY = colors.HexColor("#0284C7")
    C_ACCENT = colors.HexColor("#06B6D4")
    C_TEXT = colors.HexColor("#1E293B")
    C_MUTED = colors.HexColor("#64748B")
    C_BG_LIGHT = colors.HexColor("#F8FAFC")
    C_SUCCESS = colors.HexColor("#059669")
    C_WARNING = colors.HexColor("#D97706")
    C_DANGER = colors.HexColor("#DC2626")

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=C_PRIMARY,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=C_SECONDARY,
        spaceAfter=15,
    )
    h1_style = ParagraphStyle(
        'Heading1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=C_PRIMARY,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=C_SECONDARY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=C_TEXT,
        spaceAfter=6,
    )
    body_bold = ParagraphStyle(
        'BodyBold',
        parent=body_style,
        fontName='Helvetica-Bold',
    )
    th_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white,
    )
    code_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#0F172A"),
    )
    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1E293B"),
    )

    story = []

    # =========================================================================
    # HEADER & METADATA BANNER
    # =========================================================================
    story.append(Paragraph("VAT Enterprise: Day 2 Operations", title_style))
    story.append(Paragraph("ClickHouse & Redpanda Cut-Over, Chaos Engineering, GitOps & Strangler Fig UI", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=C_SECONDARY, spaceBefore=0, spaceAfter=10))

    meta_table_data = [
        [
            Paragraph("<b>Target Environment:</b> Production / Staging", body_style),
            Paragraph("<b>Architecture:</b> Event-Driven CQRS", body_style),
            Paragraph("<b>Execution Window:</b> Weeks 1–Month 2", body_style),
        ],
        [
            Paragraph("<b>SLA Commitment:</b> 99.999% Zero-Downtime", body_style),
            Paragraph("<b>Orchestration:</b> ArgoCD & GitOps", body_style),
            Paragraph("<b>Status:</b> Approved for Execution", body_style),
        ],
    ]
    meta_table = Table(meta_table_data, colWidths=[170, 170, 164])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # =========================================================================
    # 1. EXECUTIVE SUMMARY & ROADMAP
    # =========================================================================
    story.append(Paragraph("1. Executive Summary & Operational Roadmap", h1_style))
    story.append(Paragraph(
        "Following the successful stabilization of the foundational data models and compute isolation, "
        "VAT Enterprise is transitioning to <b>Day 2 Operations</b>. This implementation plan governs the "
        "zero-downtime cut-over to ClickHouse and Redpanda, resilience verification via Chaos Engineering, "
        "declarative GitOps pipeline enforcement, and the final migration of the NOC UI to Next.js 14 and TanStack Virtual.",
        body_style
    ))

    roadmap_data = [
        [
            Paragraph("Phase & Timeline", th_style),
            Paragraph("Core Objectives & Deliverables", th_style),
            Paragraph("Safety & Rollback Protocol", th_style),
        ],
        [
            Paragraph("<b>Step 1 (Weeks 1-2)</b><br/>ClickHouse & Redpanda Cut-Over", body_style),
            Paragraph("• Deploy Redpanda (3-node) & ClickHouse to <code>vat-staging</code>.<br/>• Configure Vector.dev dual-sink mirror.<br/>• Verify 100k EPS Kafka Engine consumption.", body_style),
            Paragraph("<font color='#059669'><b>Zero Impact</b></font>: Vector continues streaming to legacy REST store concurrently.", body_style),
        ],
        [
            Paragraph("<b>Step 2 (Week 3)</b><br/>Chaos Engineering & Resiliency", body_style),
            Paragraph("• Inject Chaos Mesh fault tests (PodKill & Network Partitions).<br/>• Verify embedding service degradation with HTTP 503 retry headers.<br/>• Assert zero dropped batches during broker failovers.", body_style),
            Paragraph("<font color='#0284C7'><b>Sandboxed</b></font>: Isolated to <code>vat-staging</code> with automated <code>concurrencyPolicy: Forbid</code>.", body_style),
        ],
        [
            Paragraph("<b>Step 3 (Week 4)</b><br/>GitOps & CI/CD Finalization", body_style),
            Paragraph("• Restrict <code>docker-compose.yml</code> to local dev only.<br/>• Establish ArgoCD ApplicationSets for staging/prod.<br/>• GitHub Actions: Pytest, Alembic dry-run, SHA image pinning.", body_style),
            Paragraph("<font color='#059669'><b>Idempotent</b></font>: Automated dry-run migrations; zero database corruption risk on retries.", body_style),
        ],
        [
            Paragraph("<b>Step 4 (Month 2)</b><br/>Strangler Fig UI Cut-Over", body_style),
            Paragraph("• Point Next.js App Router at ClickHouse analytics.<br/>• Port Vanilla JS console to React Query + TanStack Virtual.<br/>• Decommission legacy port 3001 static server.", body_style),
            Paragraph("<font color='#0284C7'><b>Instant Ingress Fallback</b></font>: Revert UI routing via Ingress annotations in < 1 sec.", body_style),
        ],
    ]
    roadmap_table = Table(roadmap_data, colWidths=[130, 240, 134])
    roadmap_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0B132B")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(roadmap_table)
    story.append(Spacer(1, 14))

    # =========================================================================
    # 2. STEP 1: CLICKHOUSE & REDPANDA CUT-OVER
    # =========================================================================
    story.append(Paragraph("2. Step 1: The ClickHouse & Redpanda Cut-Over (Weeks 1-2)", h1_style))
    story.append(Paragraph(
        "To ensure zero risk to existing production telemetry, the new streaming backbone is deployed into "
        "an isolated Kubernetes namespace (<code>vat-staging</code>). Vector.dev edge collectors mirror incoming "
        "syslog streams to both the legacy REST store (Destination A) and the new Redpanda Kafka cluster (Destination B).",
        body_style
    ))

    story.append(Paragraph("A. Vector.dev Dual-Sink Mirror Configuration (<code>config/vector/vector.toml</code>)", h2_style))
    vector_box = [
        [
            Paragraph(
                "<b># Destination A: Legacy Production Ingestion (Zero Impact)</b><br/>"
                "[sinks.legacy_production_sink]<br/>"
                "type = 'http'<br/>"
                "inputs = ['normalize_telemetry']<br/>"
                "uri = 'http://vat-backend-service.vat-system.svc.cluster.local:8000/telemetry/ingest'<br/>"
                "buffer.type = 'memory'<br/>"
                "buffer.when_full = 'drop_newest'  # Guarantees router UDP socket never blocks<br/><br/>"
                "<b># Destination B: New Redpanda Event Streaming Backbone</b><br/>"
                "[sinks.redpanda_staging_sink]<br/>"
                "type = 'kafka'<br/>"
                "inputs = ['normalize_telemetry']<br/>"
                "bootstrap_servers = 'vat-redpanda-staging-service.vat-staging.svc.cluster.local:9092'<br/>"
                "topic = 'vat.telemetry.parsed'<br/>"
                "buffer.type = 'disk'<br/>"
                "buffer.max_size = 10737418240  # 10 GB disk buffer to isolate staging backpressure",
                code_style
            )
        ]
    ]
    v_table = Table(vector_box, colWidths=[504])
    v_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(v_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("B. ClickHouse Kafka Engine & 4-Consumer Materialized View", h2_style))
    ch_box = [
        [
            Paragraph(
                "<b>-- High-Throughput Kafka Engine Queue (65k Micro-Batches)</b><br/>"
                "CREATE TABLE vat_telemetry.telemetry_kafka_queue (...)<br/>"
                "ENGINE = Kafka<br/>"
                "SETTINGS<br/>"
                "  kafka_broker_list = 'vat-redpanda-staging-service.vat-staging.svc.cluster.local:9092',<br/>"
                "  kafka_topic_list = 'vat.telemetry.parsed',<br/>"
                "  kafka_group_name = 'clickhouse-staging-consumer-group',<br/>"
                "  kafka_num_consumers = 4, kafka_max_block_size = 65536, kafka_poll_timeout_ms = 500;<br/><br/>"
                "<b>-- Continuous Ingestion Materialized View to MergeTree</b><br/>"
                "CREATE MATERIALIZED VIEW vat_telemetry.telemetry_kafka_mv TO vat_telemetry.telemetry_events AS<br/>"
                "SELECT * FROM vat_telemetry.telemetry_kafka_queue;",
                code_style
            )
        ]
    ]
    ch_table = Table(ch_box, colWidths=[504])
    ch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(ch_table)
    story.append(Spacer(1, 14))

    story.append(PageBreak())

    # =========================================================================
    # 3. STEP 2: CHAOS ENGINEERING & RESILIENCY PROVING
    # =========================================================================
    story.append(Paragraph("3. Step 2: Chaos Engineering & Resiliency Proving (Week 3)", h1_style))
    story.append(Paragraph(
        "A distributed system is only as reliable as its tested failure modes. Using Chaos Mesh, automated "
        "fault-injection experiments validate system behavior under harsh carrier network anomalies.",
        body_style
    ))

    chaos_scenarios_data = [
        [
            Paragraph("Failure Scenario", th_style),
            Paragraph("Fault Injection Mechanism", th_style),
            Paragraph("Expected SLA & Recovery Assertion", th_style),
        ],
        [
            Paragraph("<b>Redpanda Broker Leader Kill</b>", body_style),
            Paragraph("<code>PodChaos (action: pod-kill)</code> targeting active Raft leader pod during 100k EPS stream.", body_style),
            Paragraph("• Raft leader election completes in < 3s.<br/>• Vector switches to 10GB disk spool.<br/>• <b>0 dropped datagrams</b>.", body_style),
        ],
        [
            Paragraph("<b>ClickHouse Network Partition</b>", body_style),
            Paragraph("<code>NetworkChaos (action: partition)</code> isolating ClickHouse from Redpanda for 60 seconds.", body_style),
            Paragraph("• Redpanda holds topic offsets safely.<br/>• ClickHouse drains 6M event backlog upon reconnection in < 15s.", body_style),
        ],
        [
            Paragraph("<b>Embedding Service Worker Crash</b>", body_style),
            Paragraph("Termination of all <code>embedding_service</code> pods while concurrent RAG queries execute.", body_style),
            Paragraph("• API throws graceful HTTP 503 with <code>Retry-After: 3</code>.<br/>• Instant deterministic SHA-256 fallback prevents 500s.<br/>• Zero web server crash.", body_style),
        ],
    ]
    chaos_table = Table(chaos_scenarios_data, colWidths=[130, 180, 194])
    chaos_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0B132B")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(chaos_table)
    story.append(Spacer(1, 14))

    # =========================================================================
    # 4. STEP 3: GITOPS & CI/CD FINALIZATION
    # =========================================================================
    story.append(Paragraph("4. Step 3: GitOps & CI/CD Finalization (Week 4)", h1_style))
    story.append(Paragraph(
        "Production deployment is strictly decoupled from manual developer interventions. "
        "<code>docker-compose.yml</code> is relegated to local development only, while ArgoCD "
        "continuously reconciles the live Kubernetes cluster state against the Git repository.",
        body_style
    ))

    gitops_features = [
        [
            Paragraph("<b>1. Declarative ArgoCD AppSets</b>", body_bold),
            Paragraph("<code>k8s/gitops/argocd-appset.yaml</code> manages <code>vat-staging</code> and <code>vat-system</code> with automated pruning, self-healing, and wave-sequenced rollout.", body_style),
        ],
        [
            Paragraph("<b>2. Automated PreSync Migrations</b>", body_bold),
            Paragraph("Alembic schema migrations run as an isolated Kubernetes <code>PreSync</code> Job. Database upgrades dry-run and apply idempotently before application pods update.", body_style),
        ],
        [
            Paragraph("<b>3. Immutable Git SHA Tagging</b>", body_bold),
            Paragraph("GitHub Actions builds containers tagged with <code>${{ github.sha }}</code>, pinning exact artifact hashes in deployment manifests with zero mutable <code>latest</code> tags.", body_style),
        ],
    ]
    gitops_table = Table(gitops_features, colWidths=[160, 344])
    gitops_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(gitops_table)
    story.append(Spacer(1, 14))

    # =========================================================================
    # 5. STEP 4: STRANGLER FIG THE UI
    # =========================================================================
    story.append(Paragraph("5. Step 4: Strangler Fig the UI (Month 2)", h1_style))
    story.append(Paragraph(
        "The legacy Vanilla JS console is aggressively replaced using the Strangler Fig pattern. "
        "The Next.js 14 App Router shell acts as the authoritative user gateway, executing virtualized log feeds "
        "and querying ClickHouse analytical time-series endpoints directly.",
        body_style
    ))

    ui_tech_data = [
        [
            Paragraph("Architecture Component", th_style),
            Paragraph("Implementation Details & Performance Advantage", th_style),
        ],
        [
            Paragraph("<b>TanStack Virtual Feed</b>", body_style),
            Paragraph("Calculates viewport offsets to mount only ~30 active DOM rows, allowing 100,000+ streaming events in memory without DOM layout thrashing.", body_style),
        ],
        [
            Paragraph("<b>React Query Hydration</b>", body_style),
            Paragraph("Stale-while-revalidate background polling for backend health, TAC audit history, and optimistic mutations for RAG troubleshooting.", body_style),
        ],
        [
            Paragraph("<b>Legacy Decommissioning</b>", body_style),
            Paragraph("30-day grace period with <code>/legacy-console</code> routing, followed by complete sunset of the port 3001 static container.", body_style),
        ],
    ]
    ui_table = Table(ui_tech_data, colWidths=[150, 354])
    ui_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0B132B")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(ui_table)
    story.append(Spacer(1, 14))

    # =========================================================================
    # 6. BLAST RADIUS & SRE ASSURANCE SUMMARY
    # =========================================================================
    story.append(Paragraph("6. SRE Blast Radius & Rollback Governance", h1_style))
    blast_data = [
        [
            Paragraph("Phase", th_style),
            Paragraph("Risk Level", th_style),
            Paragraph("Production Failure Containment", th_style),
            Paragraph("Automated Rollback Action", th_style),
        ],
        [
            Paragraph("<b>Step 1</b>", body_style),
            Paragraph("<font color='#059669'><b>NEGLIGIBLE</b></font>", body_style),
            Paragraph("Shadow staging namespace; Vector memory drop queue protects legacy socket.", body_style),
            Paragraph("<code>kubectl delete ns vat-staging</code>", code_style),
        ],
        [
            Paragraph("<b>Step 2</b>", body_style),
            Paragraph("<font color='#D97706'><b>MODERATE</b></font>", body_style),
            Paragraph("Chaos Mesh strictly bound to <code>vat-staging</code>; prod traffic excluded.", body_style),
            Paragraph("<code>kubectl delete podchaos,networkchaos --all -n vat-staging</code>", code_style),
        ],
        [
            Paragraph("<b>Step 3</b>", body_style),
            Paragraph("<font color='#059669'><b>LOW</b></font>", body_style),
            Paragraph("PreSync dry-run migrations prevent broken schema rollouts.", body_style),
            Paragraph("<code>argocd app rollback vat-production</code>", code_style),
        ],
        [
            Paragraph("<b>Step 4</b>", body_style),
            Paragraph("<font color='#059669'><b>LOW</b></font>", body_style),
            Paragraph("Reverse proxy forwards unmigrated sub-paths transparently.", body_style),
            Paragraph("Revert Ingress annotation to legacy pod in < 1s.", body_style),
        ],
    ]
    blast_table = Table(blast_data, colWidths=[60, 80, 194, 170])
    blast_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0B132B")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(blast_table)

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated Day 2 Operations Implementation Plan PDF at: {pdf_path}")
    return str(pdf_path)

if __name__ == "__main__":
    generate_pdf()
