"""
Detailed READ-ONLY Frontend & API Weather UI Debug Script.
Parses app.js, index.html, main.py, and POST /predict/ JSON response.
"""

from pathlib import Path
import json
import urllib.request
import re

BASE_DIR = Path(__file__).resolve().parent.parent

def inspect_frontend_details():
    print("==================================================================================")
    print(" DETAILED FRONTEND ANALYSIS OF WEATHER FUNCTIONS & CARDS")
    print("==================================================================================\n")

    app_js_file = (BASE_DIR / "../frontend/app.js").resolve()
    html_file = (BASE_DIR / "../frontend/index.html").resolve()

    js_text = app_js_file.read_text(encoding="utf-8", errors="ignore")
    html_text = html_file.read_text(encoding="utf-8", errors="ignore")

    # Find all function definitions in app.js
    functions = re.findall(r'function\s+([a-zA-Z0-9_]+)\s*\(', js_text)
    print(f"Functions defined in app.js ({len(functions)}):")
    for fn in functions:
        if "weather" in fn.lower() or "card" in fn.lower() or "render" in fn.lower():
            print(f"   - {fn}")

    print("\n----------------------------------------------------------------------------------")
    print("Searching for weather fetch calls in app.js:")
    fetches = [line.strip() for line in js_text.splitlines() if "fetch(" in line or "/weather" in line or "/predict" in line]
    for ft in fetches:
        print(f"   - {ft[:120]}")

    print("\n----------------------------------------------------------------------------------")
    print("Searching for HTML container elements in index.html:")
    ids = re.findall(r'id=["\']([^"\']+)["\']', html_text)
    print(f"IDs in index.html: {ids}")

def test_live_api_endpoint():
    print("\n==================================================================================")
    print(" LIVE API REQUEST TO /predict/ & JSON FIELD VERIFICATION")
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
            print(f"Has 'regional_weather_impact': {'regional_weather_impact' in data}")
            if "regional_weather_impact" in data:
                reg = data["regional_weather_impact"]
                print(f"Payload keys: {list(reg.keys())}")
                print(f"Growing regions present: {list(reg.get('growing_region_weather', {}).get('regions', {}).keys())}")
    except Exception as e:
        print(f"API Error: {e}")

if __name__ == "__main__":
    inspect_frontend_details()
    test_live_api_endpoint()
