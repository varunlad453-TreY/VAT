#!/usr/bin/env python3
r"""
==============================================================================
Executive PDF Generator: Month 1 Zero-Trust Security & Dynamic Secrets Plan
Theme: VAT Enterprise Carrier-Grade Zero-Trust, mTLS Everywhere, Vault + ESO
Target: G:\VAT Daily\Implementation Plans\07_Implementation_Plan_Zero_Trust_Security_mTLS_and_Dynamic_Secrets.pdf
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
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable, Flowable
)
from reportlab.pdfgen import canvas

# ==============================================================================
# NUMBERED CANVAS WITH TEMPLATE RUNNING HEADERS & FOOTERS (ZERO OVERLAP)
# ==============================================================================
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
        
        # Primary Top Accent Bar (Navy + Cyan split)
        self.setFillColor(colors.HexColor("#0B132B"))
        self.rect(0, letter[1] - 8, letter[0], 8, fill=True, stroke=False)
        self.setFillColor(colors.HexColor("#0284C7"))
        self.rect(0, letter[1] - 8, letter[0] * 0.38, 8, fill=True, stroke=False)

        # Running Top Header (Pages > 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(54, letter[1] - 28, "VAT ENTERPRISE: ZERO-TRUST SECURITY & DYNAMIC SECRETS")
            self.setFont("Helvetica", 8)
            self.drawRightString(letter[0] - 54, letter[1] - 28, "MONTH 1 IMPLEMENTATION PLAN: APPROVED")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.75)
            self.line(54, letter[1] - 34, letter[0] - 54, letter[1] - 34)

        # Running Footer (All pages)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(54, 45, letter[0] - 54, 45)

        # Dynamic Footer Calculation to Prevent Any Text Collision
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#0B132B"))
        audit_tag = "ZERO-TRUST AUDIT: APPROVED (OPTION A)"
        self.drawString(54, 32, audit_tag)
        tag_width = self.stringWidth(audit_tag, "Helvetica-Bold", 8)

        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        # Draw subtitle with clean 10pt buffer after the bold audit tag
        self.drawString(54 + tag_width + 10, 32, "•  Micro-Segmented Namespaces  •  Istio mTLS  •  Vault + ESO")

        page_str = f"Page {self._pageNumber} of {page_count}"
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#0B132B"))
        self.drawRightString(letter[0] - 54, 32, page_str)
        self.restoreState()


# ==============================================================================
# DIAGRAM 1: STEP-BY-STEP TACTICAL ARCHITECTURE (PIXEL-PERFECT VECTOR FLOWCHART)
# ==============================================================================
class TacticalArchitectureDiagram(Flowable):
    """
    Renders the exact Step-by-Step Tactical Architecture for Option A:
    Vector, Redpanda, Embedding Worker, and Storage Namespaces with STRICT mTLS
    and dedicated security assertion banners. Zero overlapping labels.
    """
    def __init__(self, width=504, height=210):
        super().__init__()
        self.width = width
        self.height = height

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()

        # Canvas bounding box background
        c.setFillColor(colors.HexColor("#F8FAFC"))
        c.setStrokeColor(colors.HexColor("#CBD5E1"))
        c.setLineWidth(0.75)
        c.roundRect(0, 0, self.width, self.height, 6, fill=True, stroke=True)

        # -------------------------------------------------------------
        # 1. Namespace Cards (Option A Micro-Segmentation)
        # -------------------------------------------------------------
        # Box A: vat-vector (Left-Top: x=12, y=118, w=142, h=78)
        self._draw_card(
            c, x=12, y=118, w=142, h=78,
            header_title="vat-vector Namespace",
            header_color="#0284C7",
            items=[
                ("Vector DaemonSet Agent", "Helvetica-Bold", 7.5, "#0F172A"),
                ("SA: vat-vector-sa", "Helvetica", 6.5, "#334155"),
                ("Inbound: 514 (Syslog), 8088", "Courier", 6, "#64748B"),
                ("HostPort (No hostNetwork)", "Helvetica-Bold", 5.5, "#0284C7", True)
            ]
        )

        # Box B: vat-embedding (Left-Bottom: x=12, y=34, w=142, h=76)
        self._draw_card(
            c, x=12, y=34, w=142, h=76,
            header_title="vat-embedding Namespace",
            header_color="#6366F1",
            items=[
                ("Embedding Worker Pool", "Helvetica-Bold", 7.5, "#0F172A"),
                ("SA: vat-embedding-sa", "Helvetica", 6.5, "#334155"),
                ("Port: 8001 (Inference)", "Courier", 6, "#64748B"),
                ("Decoupled GPU/CPU Pool", "Helvetica-Bold", 5.5, "#6366F1", True)
            ]
        )

        # Box C: vat-redpanda (Center: x=184, y=34, w=142, h=162)
        self._draw_card(
            c, x=184, y=34, w=142, h=162,
            header_title="vat-redpanda Namespace",
            header_color="#059669",
            is_highlight=True,
            items=[
                ("Redpanda 3-Broker Cluster", "Helvetica-Bold", 8, "#0F172A"),
                ("SA: vat-redpanda-sa", "Helvetica", 6.5, "#334155"),
                ("Kafka: 9092  |  RPC: 33145", "Courier", 6.5, "#059669"),
                ("Headless StatefulSet", "Helvetica", 6, "#64748B"),
                ("appProtocol: tcp (No Sniff)", "Courier", 5.5, "#475569"),
                ("---", "", 0, ""),
                ("STRICT Ingress Policy:", "Helvetica-Bold", 6.5, "#065F46"),
                ("• Allow: vat-vector-sa", "Helvetica", 6, "#334155"),
                ("• Allow: vat-embedding-sa", "Helvetica", 6, "#334155"),
                ("PeerAuthentication: STRICT", "Helvetica-Bold", 5.5, "#059669", True)
            ]
        )

        # Box D: vat-storage (Right: x=350, y=34, w=142, h=162)
        self._draw_card(
            c, x=350, y=34, w=142, h=162,
            header_title="vat-storage Namespace",
            header_color="#0F172A",
            items=[
                ("PostgreSQL 16", "Helvetica-Bold", 7.5, "#0F172A"),
                ("• FORCE ROW LEVEL SECURITY", "Helvetica", 6, "#334155"),
                ("• Ephemeral Dynamic Roles", "Helvetica", 6, "#334155"),
                ("---", "", 0, ""),
                ("ClickHouse 24.3 Server", "Helvetica-Bold", 7.5, "#0F172A"),
                ("• SQL RBAC & Row Policies", "Helvetica", 6, "#334155"),
                ("• MergeTree & Kafka MV", "Helvetica", 6, "#334155"),
                ("---", "", 0, ""),
                ("Qdrant Vector DB (6333)", "Helvetica-Bold", 7.5, "#0F172A"),
                ("Default Deny: All Ingress Locked", "Helvetica-Bold", 5.5, "#0F172A", True)
            ]
        )

        # -------------------------------------------------------------
        # 2. Connection Channels & Badges (Cleanly Positioned)
        # -------------------------------------------------------------
        # Channel 1: Vector -> Redpanda (y = 157)
        c.setStrokeColor(colors.HexColor("#059669"))
        c.setLineWidth(1.5)
        c.line(154, 157, 184, 157)
        self._draw_arrow_head(c, 184, 157, direction="right", color="#059669")
        self._draw_pill_badge(c, cx=169, cy=168, text="STRICT mTLS", fill="#ECFDF5", stroke="#059669", text_color="#065F46")

        # Channel 2: Embedding -> Redpanda (y = 72)
        c.setStrokeColor(colors.HexColor("#059669"))
        c.setLineWidth(1.5)
        c.line(154, 72, 184, 72)
        self._draw_arrow_head(c, 184, 72, direction="right", color="#059669")
        self._draw_pill_badge(c, cx=169, cy=83, text="SPIFFE mTLS", fill="#ECFDF5", stroke="#059669", text_color="#065F46")

        # Channel 3: Redpanda -> Storage (y = 115)
        c.setStrokeColor(colors.HexColor("#0284C7"))
        c.setLineWidth(1.5)
        c.line(326, 115, 350, 115)
        self._draw_arrow_head(c, 350, 115, direction="right", color="#0284C7")
        self._draw_pill_badge(c, cx=338, cy=126, text="SECURE SINK", fill="#EFF6FF", stroke="#0284C7", text_color="#1E40AF")

        # -------------------------------------------------------------
        # 3. Security Assertion Banners (Isolated at Bottom, No Collisions)
        # -------------------------------------------------------------
        c.setFillColor(colors.HexColor("#FEF2F2"))
        c.setStrokeColor(colors.HexColor("#DC2626"))
        c.setLineWidth(0.75)
        c.roundRect(12, 10, 235, 18, 2, fill=True, stroke=True)
        c.setFont("Helvetica-Bold", 6)
        c.setFillColor(colors.HexColor("#991B1B"))
        c.drawString(18, 16, "[X] UNENCRYPTED TCP: DROPPED AT L4 ENVOY HANDSHAKE")

        c.setFillColor(colors.HexColor("#FEF2F2"))
        c.setStrokeColor(colors.HexColor("#DC2626"))
        c.setLineWidth(0.75)
        c.roundRect(257, 10, 235, 18, 2, fill=True, stroke=True)
        c.setFont("Helvetica-Bold", 6)
        c.setFillColor(colors.HexColor("#991B1B"))
        c.drawString(263, 16, "[X] DIRECT DB INGRESS: DENIED (L7 AUTHORIZATION POLICY)")

        c.restoreState()

    def _draw_card(self, c, x, y, w, h, header_title, header_color, items, is_highlight=False):
        c.saveState()
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.HexColor(header_color) if is_highlight else colors.HexColor("#CBD5E1"))
        c.setLineWidth(1.2 if is_highlight else 0.75)
        c.roundRect(x, y, w, h, 4, fill=True, stroke=True)

        c.setFillColor(colors.HexColor(header_color))
        c.roundRect(x, y + h - 16, w, 16, 4, fill=True, stroke=False)
        c.rect(x, y + h - 16, w, 6, fill=True, stroke=False)

        c.setFont("Helvetica-Bold", 6.5)
        c.setFillColor(colors.white)
        c.drawString(x + 6, y + h - 11, header_title)

        curr_y = y + h - 27
        for item in items:
            text = item[0]
            if text == "---":
                c.setStrokeColor(colors.HexColor("#E2E8F0"))
                c.setLineWidth(0.5)
                c.line(x + 6, curr_y + 4, x + w - 6, curr_y + 4)
                curr_y -= 8
                continue

            font_name = item[1]
            font_size = item[2]
            text_color = item[3]
            is_badge = len(item) > 4 and item[4]

            if is_badge:
                c.setFillColor(colors.HexColor("#F8FAFC"))
                c.setStrokeColor(colors.HexColor("#E2E8F0"))
                c.roundRect(x + 5, curr_y - 2, w - 10, 11, 2, fill=True, stroke=True)
                c.setFont(font_name, font_size)
                c.setFillColor(colors.HexColor(text_color))
                c.drawString(x + 9, curr_y + 1, text)
                curr_y -= 13
            else:
                c.setFont(font_name, font_size)
                c.setFillColor(colors.HexColor(text_color))
                c.drawString(x + 6, curr_y, text)
                curr_y -= (font_size + 3.5)

        c.restoreState()

    def _draw_pill_badge(self, c, cx, cy, text, fill, stroke, text_color):
        c.saveState()
        w = 36
        h = 10
        c.setFillColor(colors.HexColor(fill))
        c.setStrokeColor(colors.HexColor(stroke))
        c.setLineWidth(0.75)
        c.roundRect(cx - (w / 2), cy - (h / 2), w, h, 2, fill=True, stroke=True)
        c.setFont("Helvetica-Bold", 5)
        c.setFillColor(colors.HexColor(text_color))
        c.drawCentredString(cx, cy - 1.5, text)
        c.restoreState()

    def _draw_arrow_head(self, c, x, y, direction="right", color="#059669"):
        c.saveState()
        c.setFillColor(colors.HexColor(color))
        c.setStrokeColor(colors.HexColor(color))
        p = c.beginPath()
        if direction == "right":
            p.moveTo(x, y)
            p.lineTo(x - 4, y + 2.5)
            p.lineTo(x - 4, y - 2.5)
            p.close()
        c.drawPath(p, fill=True, stroke=False)
        c.restoreState()


# ==============================================================================
# DIAGRAM 2: PHASE 2 DYNAMIC SECRETS SEQUENCE DIAGRAM (PIXEL-PERFECT)
# ==============================================================================
class DynamicSecretsSequenceDiagram(Flowable):
    """
    Renders the exact Phase 2: Dynamic Secrets Architecture (HashiCorp Vault + ESO)
    Sequence Diagram with 5 lifelines, 7 discrete chronological operations,
    and a cleanly aligned 1-hour automatic lease rotation loop.
    """
    def __init__(self, width=504, height=225):
        super().__init__()
        self.width = width
        self.height = height

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()

        # Canvas Bounding Box
        c.setFillColor(colors.HexColor("#F8FAFC"))
        c.setStrokeColor(colors.HexColor("#CBD5E1"))
        c.setLineWidth(0.75)
        c.roundRect(0, 0, self.width, self.height, 6, fill=True, stroke=True)

        # Lifeline Coordinates (x-centers)
        participants = [
            ("Workload Pod\n(vat-backend)", 48, "#0F172A"),
            ("Kubernetes API\n(v1/Secret)", 148, "#0284C7"),
            ("External Secrets\nOperator (ESO)", 252, "#6366F1"),
            ("HashiCorp Vault\n(Dynamic DB)", 364, "#059669"),
            ("PostgreSQL /\nClickHouse", 462, "#0F172A"),
        ]

        top_y = self.height - 30
        bottom_y = 36

        # Draw Lifelines & Header Boxes
        for name, x, color_hex in participants:
            c.setStrokeColor(colors.HexColor("#CBD5E1"))
            c.setLineWidth(0.75)
            c.setDash([3, 2])
            c.line(x, top_y, x, bottom_y)
            c.setDash([])

            c.setFillColor(colors.HexColor(color_hex))
            c.roundRect(x - 40, top_y, 80, 22, 3, fill=True, stroke=False)
            
            c.setFont("Helvetica-Bold", 6.5)
            c.setFillColor(colors.white)
            lines = name.split("\n")
            if len(lines) == 1:
                c.drawCentredString(x, top_y + 7, lines[0])
            else:
                c.drawCentredString(x, top_y + 12, lines[0])
                c.setFont("Helvetica", 5.5)
                c.drawCentredString(x, top_y + 3.5, lines[1])

        # -------------------------------------------------------------
        # Sequence Messages (Numbered 1 to 7) - Floating Cleanly Above Lines
        # -------------------------------------------------------------
        steps = [
            (1, 252, 364, 168, "1. Auth via Projected SA Token (JWT)", False, "#6366F1"),
            (2, 364, 252, 149, "2. Issue Ephemeral Vault Client Token", True, "#059669"),
            (3, 252, 364, 130, "3. Request Dynamic DB Credentials", False, "#6366F1"),
            (4, 364, 462, 111, "4. Provision Dynamic Role (TTL: 4h)", False, "#059669"),
            (5, 364, 252, 92, "5. Return Ephemeral Creds & Lease ID", True, "#059669"),
            (6, 252, 148, 73, "6. Reconcile / Update v1/Secret", False, "#6366F1"),
            (7, 48, 148, 54, "7. Consume via secretKeyRef / Mount", False, "#0F172A"),
        ]

        for num, fx, tx, y, text, is_dashed, clr in steps:
            c.setStrokeColor(colors.HexColor(clr))
            c.setLineWidth(1)
            if is_dashed:
                c.setDash([3, 2])
            else:
                c.setDash([])
            
            c.line(fx, y, tx, y)
            c.setDash([])
            
            direction = "right" if tx > fx else "left"
            self._draw_arrow(c, tx, y, direction=direction, color=clr)

            mid_x = (fx + tx) / 2
            c.setFont("Helvetica-Bold", 5.8)
            c.setFillColor(colors.HexColor("#0F172A"))
            # 5pt offset above arrow line to completely avoid overlap
            c.drawCentredString(mid_x, y + 4.5, text)

        # 8. Automatic Lease Rotation Box at Bottom
        c.setFillColor(colors.HexColor("#ECFDF5"))
        c.setStrokeColor(colors.HexColor("#059669"))
        c.setLineWidth(0.75)
        c.roundRect(148, 11, 230, 18, 3, fill=True, stroke=True)
        c.setFont("Helvetica-Bold", 6)
        c.setFillColor(colors.HexColor("#065F46"))
        c.drawCentredString(263, 17.5, "Automatic Background Cycle: ESO Renews Lease / Regenerates Role Every 1h")

        c.restoreState()

    def _draw_arrow(self, c, x, y, direction="right", color="#6366F1"):
        c.saveState()
        c.setFillColor(colors.HexColor(color))
        c.setStrokeColor(colors.HexColor(color))
        p = c.beginPath()
        if direction == "right":
            p.moveTo(x, y)
            p.lineTo(x - 4, y + 2.5)
            p.lineTo(x - 4, y - 2.5)
            p.close()
        else:
            p.moveTo(x, y)
            p.lineTo(x + 4, y + 2.5)
            p.lineTo(x + 4, y - 2.5)
            p.close()
        c.drawPath(p, fill=True, stroke=False)
        c.restoreState()


# ==============================================================================
# MAIN PDF GENERATION ROUTINE
# ==============================================================================
def generate_pdf():
    output_dir = Path(r"G:\VAT Daily\Implementation Plans")
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / "07_Implementation_Plan_Zero_Trust_Security_mTLS_and_Dynamic_Secrets.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=50,
        bottomMargin=55,
    )

    styles = getSampleStyleSheet()

    # Brand Colors matching template
    C_PRIMARY = colors.HexColor("#0B132B")
    C_SECONDARY = colors.HexColor("#0284C7")
    C_SUCCESS = colors.HexColor("#059669")
    C_WARNING = colors.HexColor("#D97706")
    C_DANGER = colors.HexColor("#DC2626")
    C_TEXT = colors.HexColor("#1E293B")
    C_MUTED = colors.HexColor("#64748B")
    C_BG_LIGHT = colors.HexColor("#F8FAFC")
    C_BG_SUCCESS = colors.HexColor("#ECFDF5")

    # Typography Styles - Sized to Prevent Any Awkward Wrapping
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=C_PRIMARY,
        spaceAfter=3,
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=C_SUCCESS,
        spaceAfter=10,
    )
    h1_style = ParagraphStyle(
        'Heading1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=C_PRIMARY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=C_SECONDARY,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=C_TEXT,
        spaceAfter=3,
    )
    th_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.white,
    )
    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=C_TEXT,
    )
    code_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#0F172A"),
    )
    spiffe_code_style = ParagraphStyle(
        'SpiffeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=6.2,
        leading=8,
        textColor=colors.HexColor("#0F172A"),
    )

    story = []

    # =========================================================================
    # PAGE 1: HEADER & MASTER PLAN OVERVIEW
    # =========================================================================
    story.append(Paragraph("VAT Enterprise: Zero-Trust Security & Dynamic Secrets", title_style))
    story.append(Paragraph("Option A Micro-Segmented Mesh • Cryptographic SPIFFE mTLS • HashiCorp Vault & ESO", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=C_SUCCESS, spaceBefore=0, spaceAfter=8))

    # Architectural Verdict Banner
    verdict_box = [
        [
            Paragraph(
                "<b>ARCHITECTURAL AUDIT VERDICT: <font color='#059669'>APPROVED FOR ZERO-TRUST PRODUCTION (OPTION A)</font></b><br/>"
                "Month 1 of the Next Horizons roadmap executes <b>Option A (Micro-Segmentation)</b>, isolating workloads into dedicated "
                "Kubernetes namespaces (<code>vat-redpanda</code>, <code>vat-vector</code>, <code>vat-embedding</code>, <code>vat-storage</code>). "
                "All plaintext traffic inside the cluster is strictly blocked. Workloads authenticate via cryptographic SPIFFE X.509 certificates "
                "(Istio mTLS), and all static <code>.env</code> credentials are replaced with dynamic, short-lived secrets provisioned by HashiCorp Vault.",
                body_style
            )
        ]
    ]
    v_table = Table(verdict_box, colWidths=[504])
    v_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_BG_SUCCESS),
        ('BOX', (0, 0), (-1, -1), 1.5, C_SUCCESS),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(v_table)
    story.append(Spacer(1, 6))

    # Section 1: The Tactical Master Plan & Tooling Decisions
    story.append(Paragraph("1. The Month 1 Tactical Master Plan: Tooling Selection", h1_style))
    story.append(Paragraph(
        "A rigorous architectural trade-off evaluation selected the production security tooling for the service mesh and secrets plane:",
        body_style
    ))

    tool_matrix = [
        [
            Paragraph("Security Domain", th_style),
            Paragraph("Tool Chosen", th_style),
            Paragraph("Key Technical Capabilities", th_style),
            Paragraph("Architectural Rationale & Advantage", th_style),
        ],
        [
            Paragraph("<b>Service Mesh</b><br/>(Option A Mesh)", body_style),
            Paragraph("<b>Istio 1.22+</b><br/>(Istio CNI + Envoy)", body_style),
            Paragraph("• SPIFFE/SPIRE identity.<br/>• Native Kafka L4 filter.<br/>• East-West Gateways for DR.", body_style),
            Paragraph("Superior protocol awareness for Redpanda Kafka TCP (9092) and RPC (33145). Directly enables Month 3 cross-region replication.", body_style),
        ],
        [
            Paragraph("<b>Dynamic Secrets</b><br/>(Zero Static Secrets)", body_style),
            Paragraph("<b>HashiCorp Vault + ESO</b>", body_style),
            Paragraph("• Database Secrets Engine.<br/>• Projected SA JWT auth.<br/>• Automated 1h rotation.", body_style),
            Paragraph("Eliminates hardcoded credentials in Git/env. Ephemeral DB roles auto-expire after 4h. No heavy sidecars per pod.", body_style),
        ],
        [
            Paragraph("<b>Data Plane RBAC</b><br/>(Storage Defense)", body_style),
            Paragraph("<b>Postgres 16 RLS & ClickHouse RBAC</b>", body_style),
            Paragraph("• <code>FORCE ROW LEVEL SECURITY</code>.<br/>• SQL-driven ClickHouse users.<br/>• Tenant query quotas.", body_style),
            Paragraph("Multi-tenant isolation enforced at database kernel level. Prevents cross-tenant leaks even if backend code has vulnerabilities.", body_style),
        ],
    ]
    t_table = Table(tool_matrix, colWidths=[90, 110, 140, 164])
    t_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0B132B")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_table)
    story.append(Spacer(1, 6))

    # Section 2: Step-by-Step Tactical Architecture (Diagram 1)
    story.append(Paragraph("2. Step-by-Step Tactical Architecture: Option A Micro-Segmented Mesh", h1_style))
    story.append(Paragraph(
        "Workloads are partitioned into isolated Kubernetes namespaces with cryptographic SPIFFE X.509 mTLS enforcement:",
        body_style
    ))
    story.append(Spacer(1, 2))
    story.append(TacticalArchitectureDiagram(width=504, height=210))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: SERVICE MESH EXECUTION & PHASE 2 DYNAMIC SECRETS
    # =========================================================================
    story.append(Paragraph("A. STRICT mTLS & Zero-Trust Authorization Policy Rules", h2_style))
    story.append(Paragraph(
        "Under <code>PeerAuthentication (mode: STRICT)</code>, non-mTLS traffic is rejected at the Envoy handshake. "
        "Explicit <code>AuthorizationPolicy</code> rules enforce least-privilege service-to-service communication:",
        body_style
    ))

    # Formatted with widened SPIFFE column to ensure zero syllable wrapping
    policy_rules = [
        [
            Paragraph("Target Namespace", th_style),
            Paragraph("Port / Protocol", th_style),
            Paragraph("Authorized Source Principal (SPIFFE Identity)", th_style),
            Paragraph("Enforcement Action", th_style),
        ],
        [
            Paragraph("<code>vat-redpanda</code>", body_style),
            Paragraph("TCP 9092 (Kafka)", body_style),
            Paragraph("<code>spiffe://cluster.local/ns/vat-vector/sa/vat-vector-sa</code>", spiffe_code_style),
            Paragraph("<font color='#059669'><b>ALLOW (Ingest)</b></font>", body_style),
        ],
        [
            Paragraph("<code>vat-redpanda</code>", body_style),
            Paragraph("TCP 9092 (Kafka)", body_style),
            Paragraph("<code>spiffe://cluster.local/ns/vat-embedding/sa/vat-embedding-sa</code>", spiffe_code_style),
            Paragraph("<font color='#059669'><b>ALLOW (Consume)</b></font>", body_style),
        ],
        [
            Paragraph("<code>vat-redpanda</code>", body_style),
            Paragraph("All Ports", body_style),
            Paragraph("Any unauthenticated or plaintext connection", body_style),
            Paragraph("<font color='#DC2626'><b>DENY / DROP (L4)</b></font>", body_style),
        ],
        [
            Paragraph("<code>vat-storage</code>", body_style),
            Paragraph("TCP 5432, 8123, 6333", body_style),
            Paragraph("Unauthorized namespaces (e.g. edge vector agent)", body_style),
            Paragraph("<font color='#DC2626'><b>DENY (Default Deny)</b></font>", body_style),
        ],
    ]
    pol_table = Table(policy_rules, colWidths=[85, 75, 254, 90])
    pol_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0B132B")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(pol_table)
    story.append(Spacer(1, 6))

    # Phase 2: Dynamic Secrets Architecture (HashiCorp Vault + ESO)
    story.append(Paragraph("3. Phase 2: Dynamic Secrets Architecture (HashiCorp Vault + ESO)", h1_style))
    story.append(Paragraph(
        "All static database passwords and <code>.env</code> credentials are eliminated. Dynamic credentials with a 4-hour lease "
        "are generated on-demand by Vault and reconciled by the External Secrets Operator into native Kubernetes secrets:",
        body_style
    ))
    story.append(Spacer(1, 2))
    story.append(DynamicSecretsSequenceDiagram(width=504, height=225))
    story.append(Spacer(1, 6))

    # Dynamic Secrets Mandate Box
    vault_box = [
        [
            Paragraph(
                "<b>Vault Lease Policy & Operator Lifecycle:</b><br/>"
                "• <b>Zero Static Root Tokens:</b> ESO authenticates to Vault via Kubernetes Projected ServiceAccount Tokens (JWT).<br/>"
                "• <b>Ephemeral Database Users:</b> Vault executes <code>CREATE ROLE \"v-k8s-vat-xxx\" VALID UNTIL 'NOW + 4h'</code>.<br/>"
                "• <b>Automatic 1-Hour Secret Rotation:</b> ESO synchronizes credentials to <code>vat-database-credentials</code> every 3600s.",
                callout_style
            )
        ]
    ]
    vlt_table = Table(vault_box, colWidths=[504])
    vlt_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ('BOX', (0, 0), (-1, -1), 1, C_SECONDARY),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(vlt_table)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: MANIFEST FILE MAPPING, DATABASE RLS & VERIFICATION SIGN-OFF
    # =========================================================================
    story.append(Paragraph("4. Declarative Manifest Directory Layout & GitOps Mapping", h1_style))
    story.append(Paragraph(
        "All security configurations are 100% declarative and version-controlled under <code>k8s/security/</code>:",
        body_style
    ))

    # Sized so all repo paths fit cleanly on a single line with zero awkward character wrapping
    manifest_data = [
        [
            Paragraph("Component / Layer", th_style),
            Paragraph("Exact Repository Path", th_style),
            Paragraph("Scope & Technical Function", th_style),
        ],
        [
            Paragraph("<b>Istio Helm Override</b>", body_style),
            Paragraph("<code>k8s/security/mesh/istio-helm-values.yaml</code>", code_style),
            Paragraph("Enables Istio CNI, auto-sidecar injection, global STRICT mTLS.", body_style),
        ],
        [
            Paragraph("<b>PeerAuthentication</b>", body_style),
            Paragraph("<code>k8s/security/mesh/peer-authentication.yaml</code>", code_style),
            Paragraph("Enforces STRICT mTLS across redpanda, embedding, vector namespaces.", body_style),
        ],
        [
            Paragraph("<b>AuthorizationPolicy</b>", body_style),
            Paragraph("<code>k8s/security/mesh/authorization-policies.yaml</code>", code_style),
            Paragraph("Zero-Trust SPIFFE matching; drops all unauthorized or plaintext TCP.", body_style),
        ],
        [
            Paragraph("<b>ESO SecretStore</b>", body_style),
            Paragraph("<code>k8s/security/secrets/vault-secret-store.yaml</code>", code_style),
            Paragraph("Binds Kubernetes ServiceAccount to HashiCorp Vault auth/kubernetes.", body_style),
        ],
        [
            Paragraph("<b>ExternalSecret Specs</b>", body_style),
            Paragraph("<code>k8s/security/secrets/external-secrets.yaml</code>", code_style),
            Paragraph("Dynamic credential synchronization for PostgreSQL & ClickHouse.", body_style),
        ],
        [
            Paragraph("<b>Postgres RLS Policies</b>", body_style),
            Paragraph("<code>k8s/security/database/postgres-rls-policies.sql</code>", code_style),
            Paragraph("<code>FORCE ROW LEVEL SECURITY</code> on chunks, documents, queries.", body_style),
        ],
    ]
    man_table = Table(manifest_data, colWidths=[115, 230, 159])
    man_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0B132B")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(man_table)
    story.append(Spacer(1, 8))

    # Section 5: Verification & Day-4 Sign-Off Checklist
    story.append(Paragraph("5. Zero-Trust Security Readiness Sign-Off Checklist", h1_style))
    checklist_data = [
        [
            Paragraph("Verification Dimension", th_style),
            Paragraph("Target Specification", th_style),
            Paragraph("Observed Result / Verification", th_style),
            Paragraph("Status", th_style),
        ],
        [
            Paragraph("Mesh mTLS Encryption", body_style),
            Paragraph("100% Inter-Pod TCP Encrypted", body_style),
            Paragraph("STRICT mTLS verified via <code>istioctl tls-check</code>", body_style),
            Paragraph("<font color='#059669'><b>VERIFIED</b></font>", body_style),
        ],
        [
            Paragraph("Plaintext Rejection", body_style),
            Paragraph("0 unencrypted packets admitted", body_style),
            Paragraph("Connection reset by peer on non-sidecar test pod", body_style),
            Paragraph("<font color='#059669'><b>VERIFIED</b></font>", body_style),
        ],
        [
            Paragraph("Vault Dynamic DB Roles", body_style),
            Paragraph("4h TTL ephemeral credentials", body_style),
            Paragraph("Postgres role auto-revoked after expiration", body_style),
            Paragraph("<font color='#059669'><b>VERIFIED</b></font>", body_style),
        ],
        [
            Paragraph("ESO Secret Synchronization", body_style),
            Paragraph("Automatic refresh interval = 1h", body_style),
            Paragraph("<code>v1/Secret</code> updated with zero pod disruption", body_style),
            Paragraph("<font color='#059669'><b>VERIFIED</b></font>", body_style),
        ],
        [
            Paragraph("PostgreSQL Kernel RLS", body_style),
            Paragraph("Tenant-isolated row queries", body_style),
            Paragraph("Cross-tenant queries return 0 rows under RLS test", body_style),
            Paragraph("<font color='#059669'><b>VERIFIED</b></font>", body_style),
        ],
    ]
    chk_table = Table(checklist_data, colWidths=[130, 130, 164, 80])
    chk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0B132B")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(chk_table)

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated Month 1 Zero-Trust PDF at: {pdf_path}")
    return str(pdf_path)


if __name__ == "__main__":
    generate_pdf()
