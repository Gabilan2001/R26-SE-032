"""Generate a farmer-facing monitoring PDF from stored case facts."""

from __future__ import annotations

import io
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _pct(score: Any) -> str:
    try:
        return f"{round(float(score) * 100.0, 1):g}%"
    except (TypeError, ValueError):
        return "n/a"


def _safe(text: Any, default: str = "—") -> str:
    if text is None:
        return default
    s = str(text).strip()
    return s if s else default


def build_monitoring_report_pdf(
    *,
    case_id: str,
    crop_part: str,
    overall_status: str,
    monitoring_summary: Optional[Dict[str, Any]],
    observations: List[Dict[str, Any]],
    farmer_insight_text: Optional[str] = None,
) -> bytes:
    """
    Build a PDF report using only stored observation values.
    Does not invent severity scores or clinical claims.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"Monitoring Report {case_id}",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=6,
        textColor=colors.HexColor("#0f0f0f"),
    )
    subtitle = ParagraphStyle(
        "ReportSub",
        parent=styles["Normal"],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"),
        spaceAfter=14,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=6,
        textColor=colors.HexColor("#1a1a1a"),
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_LEFT,
        spaceAfter=4,
    )
    small = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#666666"),
        spaceBefore=10,
    )

    crop_label = "Tomato Leaf" if crop_part.upper() == "LEAF" else "Tomato Fruit"
    summary = monitoring_summary or {}

    story: List[Any] = []
    story.append(Paragraph("Tomato Disease Monitoring Report", title_style))
    story.append(
        Paragraph(
            f"{crop_label} · Case {_safe(case_id)} · Observation-based severity tracking",
            subtitle,
        )
    )

    story.append(Paragraph("Overall result", h2))
    story.append(Paragraph(f"Overall status: <b>{_safe(overall_status)}</b>", body))
    if summary:
        story.append(
            Paragraph(
                f"Initial: <b>{_safe(summary.get('initial_severity_pct'))}%</b> &nbsp;&nbsp; "
                f"Peak: <b>{_safe(summary.get('peak_severity_pct'))}%</b> &nbsp;&nbsp; "
                f"Final: <b>{_safe(summary.get('final_severity_pct'))}%</b>",
                body,
            )
        )
        change = summary.get("overall_change_pct")
        if change is not None:
            story.append(Paragraph(f"Overall change: <b>{change:+g}%</b>", body))
        if summary.get("severity_timeline"):
            story.append(
                Paragraph(f"Severity timeline: <b>{summary['severity_timeline']}</b>", body)
            )
        if summary.get("peak_note"):
            story.append(Paragraph(_safe(summary.get("peak_note")), body))

    if farmer_insight_text:
        story.append(Paragraph("Monitoring insight", h2))
        story.append(Paragraph(_safe(farmer_insight_text).replace("\n", "<br/>"), body))

    story.append(Paragraph("Observations", h2))
    rows = [["Obs", "Date", "Severity", "Class", "Trend", "Consistency"]]
    for i, obs in enumerate(observations):
        created = _safe(obs.get("created_at"), "")
        if "T" in created:
            created = created.split("T")[0]
        rows.append(
            [
                str(i + 1),
                created or "—",
                _pct(obs.get("severity_score")),
                _safe(obs.get("severity_class")),
                _safe(obs.get("trend")),
                _safe(obs.get("consistency_status")),
            ]
        )

    table = Table(rows, colWidths=[18 * mm, 32 * mm, 28 * mm, 22 * mm, 30 * mm, 40 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f7")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(table)

    story.append(Paragraph("Weather context (if available)", h2))
    weather_lines = []
    for i, obs in enumerate(observations):
        wx = obs.get("weather_context") or {}
        if isinstance(wx, dict) and wx.get("available"):
            details = wx.get("details") or {}
            temp = details.get("temperature")
            hum = details.get("humidity")
            weather_lines.append(
                f"Observation {i + 1}: Temp {temp if temp is not None else 'n/a'}°C · "
                f"Humidity {hum if hum is not None else 'n/a'}%"
            )
        else:
            weather_lines.append(f"Observation {i + 1}: weather not available")
    for line in weather_lines:
        story.append(Paragraph(line, body))

    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "Disclaimer: Severity values are observation-based visual estimates "
            "(OpenCV affected-area). This report is for monitoring support only and "
            "is not an expert-validated clinical diagnosis or treatment prescription. "
            "Weather is environmental context only and does not determine severity.",
            small,
        )
    )

    doc.build(story)
    return buffer.getvalue()
