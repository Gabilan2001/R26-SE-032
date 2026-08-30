"""PDF report builder tests."""

from utils.report_pdf import build_monitoring_report_pdf


def test_pdf_contains_header_bytes():
    pdf = build_monitoring_report_pdf(
        case_id="CASE-TEST01",
        crop_part="LEAF",
        overall_status="STABLE",
        monitoring_summary={
            "initial_severity_pct": 18.0,
            "peak_severity_pct": 24.0,
            "final_severity_pct": 12.0,
            "overall_change_pct": -6.0,
            "severity_timeline": "18% → 24% → 12%",
            "peak_note": "Highest severity was on Observation 2 (Day 3): 24%.",
        },
        observations=[
            {
                "created_at": "2026-08-01T10:00:00+00:00",
                "severity_score": 0.18,
                "severity_class": "LOW",
                "trend": "BASELINE",
                "consistency_status": "BASELINE",
                "weather_context": {"available": False},
            },
            {
                "created_at": "2026-08-03T10:00:00+00:00",
                "severity_score": 0.24,
                "severity_class": "LOW",
                "trend": "WORSENING",
                "consistency_status": "MATCH",
                "weather_context": {
                    "available": True,
                    "details": {"temperature": 30, "humidity": 70},
                },
            },
        ],
        farmer_insight_text="Condition looks improving based on your observations.",
    )
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 500


def test_pdf_no_provider_branding_in_bytes():
    pdf = build_monitoring_report_pdf(
        case_id="CASE-X",
        crop_part="FRUIT",
        overall_status="IMPROVING",
        monitoring_summary={"initial_severity_pct": 40, "final_severity_pct": 20},
        observations=[
            {
                "created_at": "2026-08-01T10:00:00+00:00",
                "severity_score": 0.4,
                "severity_class": "HIGH",
                "trend": "BASELINE",
                "consistency_status": "BASELINE",
            }
        ],
        farmer_insight_text="Monitoring only.",
    )
    lower = pdf.lower()
    assert b"gemini" not in lower
    assert b"openai" not in lower
