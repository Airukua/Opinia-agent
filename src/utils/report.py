from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any, Dict, List
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from datetime import datetime, timezone


# Brand palette
PRIMARY      = colors.HexColor("#1A237E")   # deep navy
ACCENT       = colors.HexColor("#1565C0")   # medium blue
ACCENT_LIGHT = colors.HexColor("#E3F2FD")   # pale blue fill
SUCCESS      = colors.HexColor("#2E7D32")   # green
WARNING      = colors.HexColor("#E65100")   # orange
DANGER       = colors.HexColor("#B71C1C")   # red
NEUTRAL      = colors.HexColor("#546E7A")   # blue-grey
GOLD         = colors.HexColor("#F9A825")   # gold highlight
BG_HEADER    = colors.HexColor("#0D1B6E")   # page header bg
DIVIDER      = colors.HexColor("#CFD8DC")   # light divider
TEXT_DARK    = colors.HexColor("#212121")
TEXT_MUTED   = colors.HexColor("#757575")
WHITE        = colors.white


# Page geometry
PAGE_W, PAGE_H = A4
MARGIN_L = 18 * mm
MARGIN_R = 18 * mm
MARGIN_T = 28 * mm
MARGIN_B = 22 * mm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R


# Styles
def _make_styles() -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    s: Dict[str, ParagraphStyle] = {}

    s["DocTitle"] = ParagraphStyle(
        "DocTitle", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=22,
        textColor=WHITE, leading=28, alignment=TA_LEFT,
        spaceAfter=4,
    )
    s["DocSubtitle"] = ParagraphStyle(
        "DocSubtitle", parent=base["Normal"],
        fontName="Helvetica", fontSize=11,
        textColor=colors.HexColor("#BBDEFB"), leading=16,
        alignment=TA_LEFT,
    )
    s["SectionHeading"] = ParagraphStyle(
        "SectionHeading", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=13,
        textColor=PRIMARY, leading=18,
        spaceBefore=10, spaceAfter=4,
    )
    s["SubHeading"] = ParagraphStyle(
        "SubHeading", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=10.5,
        textColor=ACCENT, leading=14,
        spaceBefore=8, spaceAfter=3,
    )
    s["Body"] = ParagraphStyle(
        "Body", parent=base["Normal"],
        fontName="Helvetica", fontSize=9.5,
        textColor=TEXT_DARK, leading=14,
        spaceAfter=5,
    )
    s["BodyMuted"] = ParagraphStyle(
        "BodyMuted", parent=base["Normal"],
        fontName="Helvetica", fontSize=9,
        textColor=TEXT_MUTED, leading=13,
    )
    s["KVLabel"] = ParagraphStyle(
        "KVLabel", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=9,
        textColor=NEUTRAL, leading=12,
    )
    s["TableHeader"] = ParagraphStyle(
        "TableHeader", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=9,
        textColor=WHITE, leading=12,
    )
    s["KVValue"] = ParagraphStyle(
        "KVValue", parent=base["Normal"],
        fontName="Helvetica", fontSize=9.5,
        textColor=TEXT_DARK, leading=13,
    )
    s["Tag"] = ParagraphStyle(
        "Tag", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=9,
        textColor=WHITE, alignment=TA_CENTER,
    )
    s["Footer"] = ParagraphStyle(
        "Footer", parent=base["Normal"],
        fontName="Helvetica", fontSize=8,
        textColor=TEXT_MUTED, alignment=TA_CENTER,
    )
    s["CardStat"] = ParagraphStyle(
        "CardStat", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=22,
        textColor=PRIMARY, alignment=TA_CENTER, leading=26,
    )
    s["CardLabel"] = ParagraphStyle(
        "CardLabel", parent=base["Normal"],
        fontName="Helvetica", fontSize=8.5,
        textColor=NEUTRAL, alignment=TA_CENTER, leading=12,
    )
    s["CommentText"] = ParagraphStyle(
        "CommentText", parent=base["Normal"],
        fontName="Helvetica-Oblique", fontSize=9,
        textColor=TEXT_DARK, leading=13,
    )
    s["CommentAuthor"] = ParagraphStyle(
        "CommentAuthor", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=8.5,
        textColor=ACCENT, leading=12,
    )
    return s


# Page header and footer
def _build_page_header(canvas, doc, video_title: str):
    canvas.saveState()
    # top bar
    canvas.setFillColor(BG_HEADER)
    canvas.rect(0, PAGE_H - 18 * mm, PAGE_W, 18 * mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, PAGE_H - 18 * mm, 5, 18 * mm, fill=1, stroke=0)
    # title text
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(WHITE)
    canvas.drawString(MARGIN_L + 6, PAGE_H - 11 * mm, "Opinia - AI agent for Youtube Comment Analysis")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#BBDEFB"))
    short_title = video_title[:70] + "\u2026" if len(video_title) > 70 else video_title
    canvas.drawRightString(PAGE_W - MARGIN_R, PAGE_H - 11 * mm, short_title)
    # footer
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawCentredString(PAGE_W / 2, 10 * mm, f"Halaman {doc.page}")
    canvas.setFillColor(DIVIDER)
    canvas.rect(MARGIN_L, 14 * mm, CONTENT_W, 0.4, fill=1, stroke=0)
    canvas.restoreState()


# Helper flowables
def _divider() -> HRFlowable:
    return HRFlowable(
        width="100%", thickness=0.8,
        color=DIVIDER, spaceAfter=6, spaceBefore=6
    )


def _section_header(text: str, styles: Dict) -> List:
    return [
        Spacer(1, 4),
        Paragraph(text, styles["SectionHeading"]),
        HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=6),
    ]


def _kv_table(rows: List[tuple], styles: Dict) -> Table:
    """Renders a 2-column key-value table with subtle striping."""
    table_data = []
    for label, value in rows:
        table_data.append([
            Paragraph(label, styles["KVLabel"]),
            Paragraph(str(value) if value is not None and value != "" else "\u2014", styles["KVValue"]),
        ])
    col_widths = [55 * mm, CONTENT_W - 55 * mm]
    tbl = Table(table_data, colWidths=col_widths, hAlign="LEFT")
    style_cmds = [
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("GRID",        (0, 0), (-1, -1), 0.3, DIVIDER),
        ("ROUNDEDCORNERS", [4]),
    ]
    for i in range(0, len(table_data), 2):
        style_cmds.append(("BACKGROUND", (0, i), (-1, i), ACCENT_LIGHT))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def _stat_cards(stats: List[tuple], styles: Dict) -> Table:
    """Renders horizontal stat cards: (value, label, color)."""
    cards = []
    for value, label, color in stats:
        cell = Table(
            [[Paragraph(str(value), styles["CardStat"])],
             [Paragraph(label, styles["CardLabel"])]],
            hAlign="CENTER",
        )
        cell.setStyle(TableStyle([
            ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND",   (0, 0), (-1, -1), WHITE),
            ("TOPPADDING",   (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
            ("BOX",          (0, 0), (-1, -1), 2, color),
            ("LINEABOVE",    (0, 0), (-1, 0), 4, color),
        ]))
        cards.append(cell)
    n = len(cards)
    gap = 4 * mm
    card_w = (CONTENT_W - gap * (n - 1)) / n
    tbl = Table([cards], colWidths=[card_w] * n, hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))
    return tbl


def _sentiment_bar(pos: int, neu: int, neg: int) -> Table:
    """Horizontal stacked bar chart for sentiment."""
    total = pos + neu + neg or 1
    pw = round(pos / total * CONTENT_W * 0.72)
    nuw = round(neu / total * CONTENT_W * 0.72)
    negw = round(neg / total * CONTENT_W * 0.72)

    bar_cells = [[" " * 3, " " * 3, " " * 3]]
    bar = Table(bar_cells, colWidths=[pw or 2, nuw or 2, negw or 2])
    bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), SUCCESS),
        ("BACKGROUND", (1, 0), (1, 0), GOLD),
        ("BACKGROUND", (2, 0), (2, 0), DANGER),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))

    def _pct(n): return f"{n/total*100:.1f}%"

    styles = _make_styles()
    legend_data = [[
        Paragraph(f"<font color='#2E7D32'>\u25cf</font>  Positif  <b>{pos}</b> ({_pct(pos)})", styles["Body"]),
        Paragraph(f"<font color='#F9A825'>\u25cf</font>  Netral  <b>{neu}</b> ({_pct(neu)})", styles["Body"]),
        Paragraph(f"<font color='#B71C1C'>\u25cf</font>  Negatif  <b>{neg}</b> ({_pct(neg)})", styles["Body"]),
    ]]
    legend = Table(legend_data, colWidths=[CONTENT_W / 3] * 3)
    legend.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))

    wrapper = Table([[bar], [legend]], colWidths=[CONTENT_W])
    wrapper.setStyle(TableStyle([
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
    ]))
    return wrapper


def _insight_block(title: str, text: str, styles: Dict, accent_color=ACCENT) -> Table:
    """Renders a labelled insight block with a left accent bar."""
    content = [
        [" ", Paragraph(f"<b>{title}</b>", styles["SubHeading"])],
        [" ", Paragraph(_md_to_html(text) if text else "\u2014", styles["Body"])],
    ]
    tbl = Table(
        content,
        colWidths=[4, CONTENT_W - 4],
        splitByRow=1,
        splitInRow=1,
    )
    tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (0, -1), accent_color),
        ("BACKGROUND",  (1, 0), (1, -1), ACCENT_LIGHT),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",(0, 0), (-1, -1), 0),
        ("TOPPADDING",  (1, 0), (1, -1), 4),
        ("BOTTOMPADDING",(1, 0), (1, -1), 4),
        ("LEFTPADDING", (1, 0), (1, -1), 6),
        ("RIGHTPADDING",(1, 0), (1, -1), 6),
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("LINEAFTER",   (0, 0), (-1, -1), 0.3, DIVIDER),
    ]))
    return tbl


def _top_comments_table(comments: List[Dict], styles: Dict) -> Table:
    """Renders top comments as a styled table."""
    header = [
        Paragraph("Penulis", styles["TableHeader"]),
        Paragraph("Komentar", styles["TableHeader"]),
        Paragraph("Likes", styles["TableHeader"]),
    ]
    rows = [header]
    for c in comments[:8]:
        text = c.get("text", "")
        rows.append([
            Paragraph(c.get("author", "\u2014"), styles["BodyMuted"]),
            Paragraph(text, styles["CommentText"]),
            Paragraph(str(c.get("like_count", 0)), styles["Body"]),
        ])
    col_widths = [28 * mm, CONTENT_W - 28 * mm - 16 * mm, 16 * mm]
    tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND",   (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR",    (0, 0), (-1, 0), WHITE),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 9),
        ("ALIGN",        (2, 0), (2, -1), "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, ACCENT_LIGHT]),
        ("GRID",         (0, 0), (-1, -1), 0.3, DIVIDER),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    tbl.setStyle(TableStyle(style_cmds))
    return tbl



# Markdown to ReportLab HTML

def _inline(text: str) -> str:
    """Apply bold and italic inline markup to already-HTML-escaped text."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"\*{2,}", "", text)
    return text


def _safe_text(text: Any) -> str:
    if text is None:
        return "\u2014"
    value = str(text).strip()
    return value if value else "\u2014"


def _format_timestamp(value: Any) -> str:
    """Normalize ISO timestamps to a human-friendly format."""
    if value is None:
        return "\u2014"
    raw = str(value).strip()
    if not raw:
        return "\u2014"
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M %Z").replace("UTC", "UTC")
    except Exception:
        return raw


def _md_to_html(text: str) -> str:
    """
    Converts LLM markdown output to ReportLab-safe HTML markup.

    Handles:
    - **bold** and *italic* inline spans
    - Numbered top-level items:  "1.  **Title.**"
    - Indented sub-bullets:      "    *   **Label:** text"
    - Top-level bullets:         "- item"
    - Standalone bold headings:  "**Heading:**"
    - Paragraph spacing from blank lines
    - Multiline ** markers (LLM formatting artifacts)
    """
    if not text:
        return "\u2014"
    out = str(text).strip()
    out = out.replace("\r\n", "\n").replace("\r", "\n")
    out = re.sub(r"\*\*([^*\n]+)\n\*\*", r"**\1**", out)
    out = out.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    lines = out.split("\n")
    rendered: List[str] = []

    for ln in lines:
        raw = ln.rstrip()
        if not raw.strip():
            rendered.append("")
            continue

        stripped = raw.lstrip()
        indent = len(raw) - len(stripped)

        # ── numbered top-level:  "1.  **Title.**" or "1. plain text"
        m = re.match(r"^(\d+)[.)]\s+(.*)", stripped)
        if m and indent == 0:
            num = m.group(1)
            content = m.group(2).strip()
            content = re.sub(r"^\*\*(.+)\*\*$", r"\1", content)
            content = _inline(content)
            rendered.append(f"<b>{num}. {content}</b>")
            continue

        # ── sub-bullet (indent >= 2): "    *   text" or "    -   text"
        m = re.match(r"^[-*\u2022]\s+(.*)", stripped)
        if m and indent >= 2:
            content = _inline(m.group(1))
            rendered.append(f"\u00a0\u00a0\u00a0\u00a0\u2022 {content}")
            continue

        # ── top-level bullet (no indent): "* text" or "- text"
        m = re.match(r"^[-*\u2022]\s+(.*)", stripped)
        if m and indent == 0:
            content = _inline(m.group(1))
            rendered.append(f"\u2022 {content}")
            continue

        # ── plain / bold-heading line
        rendered.append(_inline(stripped))

    # trim leading/trailing blank entries before joining
    while rendered and rendered[0] == "":
        rendered.pop(0)
    while rendered and rendered[-1] == "":
        rendered.pop()

    result = "<br/>".join(rendered)
    # collapse 3+ consecutive <br/> to 2
    result = re.sub(r"(<br/>){3,}", "<br/><br/>", result)
    return result


# Main report builder
def _write_pdf_report(payload: Dict[str, Any], output_path: Path) -> None:
    """Writes a human-readable PDF report from the result payload."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    styles = _make_styles()
    video_meta   = payload.get("video", {}) or {}
    run_meta     = payload.get("run_metadata", {}) or {}
    evidence     = payload.get("evidence", payload.get("evidence_snapshot", {})) or {}
    llm_insights = payload.get("llm_insights", {}) or {}

    video_title = video_meta.get("video_title", "Comment Analytics Report")

    # ── Doc template with header/footer ──────────────────────────────────────
    def _header_footer(canvas, doc):
        _build_page_header(canvas, doc, video_title)

    doc = BaseDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_T,
        bottomMargin=MARGIN_B,
    )
    frame = Frame(MARGIN_L, MARGIN_B, CONTENT_W, PAGE_H - MARGIN_T - MARGIN_B, id="main")
    template = PageTemplate(id="page", frames=[frame], onPage=_header_footer)
    doc.addPageTemplates([template])

    story = []

    # Cover block
    cover_data = [[
        Paragraph("Opinia - AI agent for Youtube Comment Analysis", styles["DocTitle"]),
        Paragraph(video_title, styles["DocSubtitle"]),
        Spacer(1, 6),
        Paragraph(
            f"Video ID: <b>{video_meta.get('video_id', '\u2014')}</b>  |  "
            f"Scraped: <b>{_format_timestamp(run_meta.get('scraped_at'))}</b>",
            styles["DocSubtitle"]
        ),
    ]]
    cover = Table([[cover_data[0]]], colWidths=[CONTENT_W])
    cover.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), BG_HEADER),
        ("LEFTPADDING",  (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING",   (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 18),
        ("LINEBEFORE",   (0, 0), (-1, -1), 5, GOLD),
    ]))
    story.append(cover)
    story.append(Spacer(1, 8))

    # Stat cards
    comment_totals = (evidence.get("comment_totals") or {}) if isinstance(evidence, dict) else {}
    total_c = comment_totals.get("total_comments") or run_meta.get("total_comments") or "\u2014"
    spam_c  = comment_totals.get("spam_comments", 0)
    toxic_c = comment_totals.get("toxic_comments", 0)

    story += _section_header("Ringkasan Statistik", styles)
    story.append(_stat_cards([
        (total_c, "Total Komentar", ACCENT),
        (spam_c,  "Komentar Spam",  NEUTRAL),
        (toxic_c, "Komentar Toxic", DANGER),
    ], styles))
    story.append(Spacer(1, 10))

    # Video metadata
    story += _section_header("Informasi Video", styles)
    story.append(_kv_table([
        ("Video ID",    video_meta.get("video_id")),
        ("Judul",       video_meta.get("video_title")),
        ("Anonimoyze", "Ya" if run_meta.get("anonymized") else "Tidak"),
        ("Waktu Scrape",_format_timestamp(run_meta.get("scraped_at"))),
    ], styles))
    story.append(Spacer(1, 8))

    # Sentiment
    sentiment_summary = None
    if isinstance(evidence, dict):
        sentiment_summary = (evidence.get("sentiment") or {}).get("summary")
    if sentiment_summary:
        dist = sentiment_summary.get("distribution") or {}
        pos  = dist.get("positive", 0)
        neu  = dist.get("neutral", 0)
        neg  = dist.get("negative", 0)

        story += _section_header("Analisis Sentimen", styles)
        story.append(_sentiment_bar(pos, neu, neg))
        story.append(Spacer(1, 6))

        score_data = sentiment_summary.get("sentiment_score", {})
        if score_data:
            score_val   = score_data.get("score", "\u2014")
            score_label = score_data.get("label", "\u2014")
            story.append(_kv_table([
                ("Skor Sentimen", f"{score_val}  ({score_label})"),
                ("Formula",       score_data.get("formula", "\u2014")),
            ], styles))
        story.append(Spacer(1, 8))

    # Topic clusters
    topic_data = evidence.get("topics", {}) if isinstance(evidence, dict) else {}
    topic_clusters = (topic_data.get("cluster_summary") or {}).get("clusters", []) if topic_data else []

    if not topic_clusters:
        raw_topics = payload.get("topics", {})
        topic_clusters = (raw_topics.get("cluster_summary") or {}).get("clusters", [])

    if topic_clusters:
        story += _section_header("Kluster Topik", styles)
        tc_data = [[
            Paragraph("Label Kluster", styles["TableHeader"]),
            Paragraph("Jumlah", styles["TableHeader"]),
        ]]
        for cl in topic_clusters:
            lbl = cl.get("topic_label") or f"Kluster {cl.get('label', '?')}"
            cnt = cl.get("cluster_size") or cl.get("count", "\u2014")
            tc_data.append([
                Paragraph(lbl, styles["Body"]),
                Paragraph(str(cnt), styles["Body"]),
            ])
        tc_tbl = Table(tc_data, colWidths=[CONTENT_W - 28 * mm, 28 * mm])
        tc_tbl.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR",    (0, 0), (-1, 0), WHITE),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, ACCENT_LIGHT]),
            ("GRID",         (0, 0), (-1, -1), 0.3, DIVIDER),
            ("TOPPADDING",   (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
            ("LEFTPADDING",  (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("ALIGN",        (1, 0), (1, -1), "CENTER"),
        ]))
        story.append(tc_tbl)
        story.append(Spacer(1, 8))

    # Top liked comments
    top_liked = None
    if isinstance(evidence, dict):
        eda = evidence.get("eda") or payload.get("eda") or {}
        top_liked = ((eda.get("engagement_analysis") or {}).get("top_liked_comments"))
    if not top_liked:
        top_liked = (payload.get("eda") or {}).get("engagement_analysis", {}).get("top_liked_comments")

    if top_liked:
        story += _section_header("Komentar Paling Disukai", styles)
        story.append(_top_comments_table(top_liked, styles))
        story.append(Spacer(1, 8))

    # LLM insights
    story.append(PageBreak())
    story += _section_header("LLM Insights", styles)
    story.append(_kv_table([
        ("Mode",  llm_insights.get("mode")),
        ("Model", llm_insights.get("model_used")),
    ], styles))
    story.append(Spacer(1, 8))

    insight_sections = [
        ("summary",           "Ringkasan Eksekutif",  ACCENT),
        ("emotional_triggers","Pemicu Emosi Utama",    DANGER),
        ("viral_formula",     "Formula Viral",         SUCCESS),
        ("audience_persona",  "Persona Audiens",       NEUTRAL),
        ("content_hooks",     "Hook & Frasa Kunci",    WARNING),
        ("opportunities",     "Peluang Konten",        SUCCESS),
        ("risks",             "Risiko",                DANGER),
        ("suggested_topics",  "Judul yang Diusulkan",  ACCENT),
    ]

    for key, title, color in insight_sections:
        value = llm_insights.get(key)
        if not value:
            continue
        story.append(_insight_block(title, _safe_text(value), styles, color))
        story.append(Spacer(1, 8))

    doc.build(story)
