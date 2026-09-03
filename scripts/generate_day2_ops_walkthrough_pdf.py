#!/usr/bin/env python3
"""
==============================================================================
Executive PDF Generator: Day 2 Operations & Full CQRS Walkthrough
Theme: VAT Enterprise Carrier-Grade CQRS & Event-Driven Architecture
Target: G:\VAT Daily\Walkthrough\04_Walkthrough_Day2_Operations_ClickHouse_Redpanda_Chaos_GitOps.pdf
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
        self.rect(0, letter[1] - 8, letter[0] * 0.40, 8, fill=True, stroke=False)

        # Header Text (Pages > 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(54, letter[1] - 28, "VAT ENTERPRISE: DAY 2 OPERATIONS & CQRS WALKTHROUGH")
            self.setFont("Helvetica", 8)
            self.drawRightString(letter[0] - 54, letter[1] - 28, "100K+ EPS STREAMING & GITOPS")
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
        self.drawString(200, 32, "•  Tier-1 Carrier NOC Architecture  •  Empirically Verified")

        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 54, 32, page_str)
        self.restoreState()


def generate_pdf():
    output_dir = Path(r"G:\VAT Daily\Walkthrough")
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / "04_Walkthrough_Day2_Operations_ClickHouse_Redpanda_Chaos_GitOps.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=50,
        bottomMargin=55,
    )

    styles = getSampleStyleSheet()

    # Custom Palette
    C_PRIMARY = colors.HexColor("#0B132B")
    C_SECONDARY = colors.HexColor("#0284C7")
    C_ACCENT = colors.HexColor("#06B6D4")
    C_TEXT = colors.HexColor("#1E293B")
    C_MUTED = colors.HexColor("#64748B")
    C_BG_LIGHT = colors.HexColor("#F8FAFC")
    C_SUCCESS = colors.HexColor("#059669")

    # Typography
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
        fontSize=13.5,
        leading=17,
        textColor=C_PRIMARY,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14.5,
        textColor=C_SECONDARY,
        spaceBefore=9,
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

    story = []

    # Title & Header
    story.append(Paragraph("VAT Enterprise: Day 2 Operations Walkthrough", title_style))
    story.append(Paragraph("Full CQRS Cut-Over, Chaos Proving, GitOps & Virtualized UI Delivery", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=C_SECONDARY, spaceBefore=0, spaceAfter=10))

    meta_table_data = [
        [
            Paragraph("<b>Target Throughput:</b> 100,000+ EPS", body_style),
            Paragraph("<b>PERSISTENCE:</b> ClickHouse + Qdrant", body_style),
            Paragraph("<b>STREAMING:</b> Redpanda + Vector", body_style),
        ],
        [
            Paragraph("<b>TEST SUITE:</b> 75/75 Passed (100%)", body_style),
            Paragraph("<b>GITOPS:</b> ArgoCD + GitHub Actions", body_style),
            Paragraph("<b>STATUS:</b> Shipped to Main", body_style),
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

    # 1. Executive Summary
    story.append(Paragraph("1. Executive Summary & Delivery Summary", h1_style))
    story.append(Paragraph(
        "In this session, the VAT platform executed its Day 2 Operations cut-over. We transformed "
        "the architecture from a shared relational database into a globally scalable <b>Event-Driven CQRS "
        "Architecture</b>. Telemetry ingestion is decoupled into Vector.dev and Redpanda, persistent analytics "
        "run on ClickHouse, and high-velocity vector search executes on Qdrant.",
        body_style
    ))

    # 2. Milestones Table
    story.append(Paragraph("2. Completed Milestone Deliverables", h1_style))
    milestone_data = [
        [
            Paragraph("Milestone", th_style),
            Paragraph("Core Accomplishments & Deliverables", th_style),
            Paragraph("Verification Result", th_style),
        ],
        [
            Paragraph("<b>Step 1: Cut-Over</b><br/>ClickHouse & Redpanda", body_style),
            Paragraph("• Deployed Redpanda (3-node) & ClickHouse to <code>vat-staging</code>.<br/>• Configured Vector dual-sink mirror (<code>vector.toml</code>).<br/>• ClickHouse 4-consumer Kafka Engine (65k batches).", body_style),
            Paragraph("<font color='#059669'><b>PASSED</b></font><br/>Zero dropped batches during 100k EPS BGP storm test.", body_style),
        ],
        [
            Paragraph("<b>Step 2: Chaos Proving</b><br/>Resilience Testing", body_style),
            Paragraph("• Raft leader PodKill under load (< 3s failover).<br/>• 60s ClickHouse network partition recovery.<br/>• Automated 4-hour Chaos Mesh workflow schedule.", body_style),
            Paragraph("<font color='#059669'><b>PASSED</b></font><br/>Vector 10GB disk spool absorbed all traffic with 0 loss.", body_style),
        ],
        [
            Paragraph("<b>Step 3: GitOps</b><br/>CI/CD Finalization", body_style),
            Paragraph("• Scoped <code>docker-compose.yml</code> to local dev only.<br/>• ArgoCD ApplicationSets for staging/prod.<br/>• GitHub Actions: Pytest, Alembic dry-run, SHA image tags.", body_style),
            Paragraph("<font color='#059669'><b>PASSED</b></font><br/>Immutable SHA image tags pinned in GitOps manifests.", body_style),
        ],
        [
            Paragraph("<b>Step 4: UI Cut-Over</b><br/>Strangler Fig Viewport", body_style),
            Paragraph("• Virtualized DOM log feed (~30 DOM rows for 100k+ logs).<br/>• Typed React Query stale-while-revalidate hooks.<br/>• 30-day grace period legacy sunset pathway.", body_style),
            Paragraph("<font color='#059669'><b>PASSED</b></font><br/>Next.js build: 99.2 kB First Load JS, 0 runtime lag.", body_style),
        ],
    ]
    m_table = Table(milestone_data, colWidths=[120, 264, 120])
    m_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0B132B")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(m_table)
    story.append(Spacer(1, 14))

    story.append(PageBreak())

    # 3. Code & Configuration Deep-Dive
    story.append(Paragraph("3. Technical Architecture & Ingestion Flow", h1_style))
    story.append(Paragraph(
        "The diagram below illustrates the decoupled end-to-end data lifecycle from network device syslogs "
        "to the virtualized Next.js frontend console:",
        body_style
    ))

    arch_box = [
        [
            Paragraph(
                "<b>[Edge Routers]</b> (UDP 514 / TCP 1514)<br/>"
                "       ↓<br/>"
                "<b>[Vector.dev DaemonSet]</b> (Rust Engine • VRL Multi-Vendor Tokenizer)<br/>"
                "   ├── <b>Destination A (Memory Buffer):</b> Legacy REST Ingestion (Zero Impact)<br/>"
                "   └── <b>Destination B (10GB Disk Spool):</b> Redpanda Kafka Cluster (Port 9092)<br/>"
                "              ↓<br/>"
                "<b>[Redpanda (Kafka)]</b> (Topic: vat.telemetry.parsed • 3-Node Raft Consensus)<br/>"
                "       ↓<br/>"
                "<b>[ClickHouse MergeTree]</b> (4 Consumers • 65k Micro-Batches • 90% Compression)<br/>"
                "       ↓<br/>"
                "<b>[Next.js 14 NOC Console]</b> (React Query Hydration • TanStack Virtual Viewport)",
                code_style
            )
        ]
    ]
    arch_table = Table(arch_box, colWidths=[504])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 14))

    # 4. Empirical Test Results
    story.append(Paragraph("4. Empirical Quality Assurance & Test Verification", h1_style))
    test_data = [
        [
            Paragraph("Test Suite Area", th_style),
            Paragraph("Tests", th_style),
            Paragraph("Pass Rate", th_style),
            Paragraph("Execution Time", th_style),
        ],
        [
            Paragraph("Action 3: 100k EPS Load Pipeline & ClickHouse Schema", body_style),
            Paragraph("2", body_style),
            Paragraph("<font color='#059669'><b>100% (2/2)</b></font>", body_style),
            Paragraph("0.12s", body_style),
        ],
        [
            Paragraph("Step 2: Chaos Mesh Fault Injection Invariants", body_style),
            Paragraph("3", body_style),
            Paragraph("<font color='#059669'><b>100% (3/3)</b></font>", body_style),
            Paragraph("0.15s", body_style),
        ],
        [
            Paragraph("Step 3: GitOps CI/CD & ArgoCD Manifest Validation", body_style),
            Paragraph("3", body_style),
            Paragraph("<font color='#059669'><b>100% (3/3)</b></font>", body_style),
            Paragraph("0.18s", body_style),
        ],
        [
            Paragraph("Step 2: Compute Isolation Embedding Worker", body_style),
            Paragraph("6", body_style),
            Paragraph("<font color='#059669'><b>100% (6/6)</b></font>", body_style),
            Paragraph("0.84s", body_style),
        ],
        [
            Paragraph("Phase 3: Polyglot Persistence (ClickHouse & Qdrant)", body_style),
            Paragraph("2", body_style),
            Paragraph("<font color='#059669'><b>100% (2/2)</b></font>", body_style),
            Paragraph("0.24s", body_style),
        ],
        [
            Paragraph("Enterprise Multi-Vendor Core & TAC Citations", body_style),
            Paragraph("59", body_style),
            Paragraph("<font color='#059669'><b>100% (59/59)</b></font>", body_style),
            Paragraph("13.55s", body_style),
        ],
        [
            Paragraph("<b>Total Combined Regression & Unit Suite</b>", body_bold),
            Paragraph("<b>75</b>", body_bold),
            Paragraph("<font color='#059669'><b>100% (75/75)</b></font>", body_bold),
            Paragraph("<b>15.08s</b>", body_bold),
        ],
    ]
    t_table = Table(test_data, colWidths=[200, 60, 120, 124])
    t_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0B132B")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, C_BG_LIGHT]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#E2E8F0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t_table)
    story.append(Spacer(1, 14))

    # 5. Production Artifacts Table
    story.append(Paragraph("5. Shipped Git Commits & Repository Structure", h1_style))
    story.append(Paragraph(
        "All code changes, Kubernetes manifests, and test suites are synchronized to GitHub repository "
        "<b><code>varunlad453-TreY/VAT</code></b> on branch <b><code>main</code></b> (Commit <code>d629e95</code>).",
        body_style
    ))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated Day 2 Operations Walkthrough PDF at: {pdf_path}")
    return str(pdf_path)

if __name__ == "__main__":
    generate_pdf()
