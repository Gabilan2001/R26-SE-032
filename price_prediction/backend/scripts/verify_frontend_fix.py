"""
Verification Script for Frontend Regional Weather Fix.
Checks live http://127.0.0.1:8000/ui/app.js?v=2 output.
"""

import urllib.request
import json

def test_frontend_live():
    print("==================================================================================")
    print(" VERIFYING LIVE SERVED FRONTEND APP.JS & PREDICT API")
    print("==================================================================================\n")

    # 1. Fetch live app.js from FastAPI
    js_url = "http://127.0.0.1:8000/ui/app.js?v=2"
    with urllib.request.urlopen(js_url) as resp:
        js_code = resp.read().decode("utf-8")
        has_old_anura_fetch = "fetch(`/weather/?location=Anuradhapura`" in js_code or "location=Anuradhapura" in js_code
        has_regional_render = "renderWeatherCard(pData.regional_weather_impact)" in js_code or "renderWeatherCard(data.regional_weather_impact)" in js_code
        
        print(f"1. Is legacy Anuradhapura fetch removed from app.js? -> {not has_old_anura_fetch}")
        print(f"2. Is regional_weather_impact passed to renderWeatherCard in app.js? -> {has_regional_render}")

    # 2. Call /predict/ for Dambulla-Wholesale
    pred_url = "http://127.0.0.1:8000/predict/"
    payload = {
        "market": "Dambulla",
        "type": "Wholesale",
        "forecast_horizon_days": 14
    }
    req = urllib.request.Request(
        pred_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        reg = data.get("regional_weather_impact", {})
        print("\n3. Live /predict/ payload for Dambulla-Wholesale:")
        print(f"   Season: {reg.get('season')}")
        print(f"   Overall Risk: {reg.get('overall_weather_risk')}")
        print(f"   Primary Region: {reg.get('primary_region')}")
        print(f"   Primary Signal: {reg.get('primary_signal')}")
        print(f"   Stations: {list(reg.get('growing_region_weather', {}).get('regions', {}).keys())}")
        print(f"   Market Storage Spoilage: {reg.get('market_storage_impact', {}).get('spoilage_risk_level')}")

if __name__ == "__main__":
    test_frontend_live()
