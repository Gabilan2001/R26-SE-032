"""
Phase 1: Weather Integration Audit Script.
Inspects current production decision engine, weather service, schemas, API routes,
and frontend files to detail existing flows, schemas, and weather logic.
"""

from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent

def audit_phase_1():
    print("==================================================================================")
    print(" PHASE 1: INSPECTION OF PRODUCTION PREDICTION & WEATHER FLOWS")
    print("==================================================================================\n")

    files_to_check = [
        "app/services/decision_engine_service.py",
        "app/services/weather_service.py",
        "app/services/anomaly_detection_service.py",
        "app/services/news_event_service.py",
        "app/services/shap_explainer_service.py",
        "app/routes/predict_routes.py",
        "app/routes/weather_routes.py",
        "app/schemas/prediction_schema.py",
        "../frontend/index.html",
        "../frontend/app.js"
    ]

    for rel_f in files_to_check:
        p = (BASE_DIR / rel_f).resolve()
        exists = p.exists()
        size_kb = (p.stat().st_size / 1024.0) if exists else 0.0
        print(f"File: {rel_f}")
        print(f"  Path: {p}")
        print(f"  Exists: {exists} ({size_kb:.1f} KB)")

    print("\nTracing Decision Engine Current Weather Logic...")
    de_file = BASE_DIR / "app/services/decision_engine_service.py"
    if de_file.exists():
        text = de_file.read_text(encoding="utf-8", errors="ignore")
        print("  Occurrences of 'weather' in decision_engine_service.py:")
        lines = [line.strip() for line in text.splitlines() if "weather" in line.lower()]
        for line in lines[:10]:
            print(f"    - {line[:100]}")

    print("\nTracing Weather Service Current Methods...")
    ws_file = BASE_DIR / "app/services/weather_service.py"
    if ws_file.exists():
        text = ws_file.read_text(encoding="utf-8", errors="ignore")
        lines = [line.strip() for line in text.splitlines() if "def " in line]
        for line in lines:
            print(f"    - {line}")

if __name__ == "__main__":
    audit_phase_1()
