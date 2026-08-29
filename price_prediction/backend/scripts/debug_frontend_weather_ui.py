"""
READ-ONLY Frontend & API Weather UI Debug Script.
Inspects frontend/index.html, frontend/app.js, main.py static routes,
and calls POST http://127.0.0.1:8000/predict/ to inspect live JSON response.
"""

from pathlib import Path
import json
import urllib.request
import re

BASE_DIR = Path(__file__).resolve().parent.parent

def inspect_frontend_code():
    print("==================================================================================")
    print(" 1, 2, 3, 4, 10, 11. FRONTEND CODE & TEMPLATE INSPECTION")
    print("==================================================================================\n")

    html_file = (BASE_DIR / "../frontend/index.html").resolve()
    app_js_file = (BASE_DIR / "../frontend/app.js").resolve()
    main_py_file = (BASE_DIR / "main.py").resolve()

    print(f"index.html path: {html_file}")
    print(f"app.js path: {app_js_file}")
    print(f"main.py path: {main_py_file}\n")

    if app_js_file.exists():
        js_text = app_js_file.read_text(encoding="utf-8", errors="ignore")
        has_build_regional = "buildRegionalWeatherCard" in js_text
        print(f"1. Does 'buildRegionalWeatherCard' exist in app.js? -> {has_build_regional}")
        
        # Search where "Weather & Storage Context" or old weather HTML is generated in app.js
        old_weather_matches = [line.strip() for line in js_text.splitlines() if "Weather & Storage Context" in line or "Growing Region Weather" in line or "Anuradhapura" in line]
        print(f"2. Old Weather text occurrences in app.js ({len(old_weather_matches)}):")
        for m in old_weather_matches:
            print(f"   - {m[:100]}")

        # Search for weather rendering calls in app.js
        calls = [line.strip() for line in js_text.splitlines() if "weather" in line.lower()]
        print(f"\n3. Weather calls/renders in app.js ({len(calls)}):")
        for c in calls[:15]:
            print(f"   - {c[:100]}")

    if html_file.exists():
        html_text = html_file.read_text(encoding="utf-8", errors="ignore")
        old_html_matches = [line.strip() for line in html_text.splitlines() if "Weather" in line or "weather" in line]
        print(f"\n4. Weather elements in index.html ({len(old_html_matches)}):")
        for m in old_html_matches:
            print(f"   - {m[:100]}")

    if main_py_file.exists():
        py_text = main_py_file.read_text(encoding="utf-8", errors="ignore")
        print("\nStatic mount configuration in main.py:")
        mount_lines = [line.strip() for line in py_text.splitlines() if "mount" in line.lower() or "static" in line.lower() or "ui" in line.lower()]
        for ml in mount_lines:
            print(f"   - {ml}")

def test_live_api_endpoint():
    print("\n==================================================================================")
    print(" 5, 6, 7. LIVE API REQUEST TO /predict/ & JSON FIELD COMPARISON")
    print("==================================================================================\n")

    url = "http://127.0.0.1:8000/predict/"
    payload = {
        "market": "Dambulla",
        "type": "Retail",
        "forecast_horizon_days": 14
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"HTTP Status: {resp.status}")
            print(f"Keys in Response Payload ({len(data)}):")
            print(f"  {list(data.keys())}\n")

            has_regional = "regional_weather_impact" in data
            print(f"5. Is 'regional_weather_impact' present in /predict/ JSON response? -> {has_regional}")

            if has_regional:
                reg_data = data["regional_weather_impact"]
                print("\n  regional_weather_impact payload structure:")
                print(f"    season: {reg_data.get('season')}")
                print(f"    overall_weather_risk: {reg_data.get('overall_weather_risk')}")
                print(f"    primary_region: {reg_data.get('primary_region')}")
                print(f"    growing_region_weather keys: {list(reg_data.get('growing_region_weather', {}).keys())}")
                print(f"    market_storage_impact keys: {list(reg_data.get('market_storage_impact', {}).keys())}")
            else:
                print("  WARNING: 'regional_weather_impact' is missing from API response!")

    except Exception as e:
        print(f"API Request Error: {e}")

if __name__ == "__main__":
    inspect_frontend_code()
    test_live_api_endpoint()
