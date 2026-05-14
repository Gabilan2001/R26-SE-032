"""
Full system check for the tomato price prediction backend.

Run from the backend folder (same directory as main.py):
    python check_system.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure imports resolve the same way as uvicorn (backend = cwd).
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.chdir(BACKEND_DIR)

from dotenv import load_dotenv

load_dotenv(BACKEND_DIR / ".env", override=True)


def _count_csv_rows(path: Path) -> int:
    """Count data rows (excluding header) without loading the whole file into RAM."""
    if not path.is_file():
        return -1
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return max(0, sum(1 for _ in handle) - 1)


def step1_file_audit() -> None:
    """STEP 1 — verify key files exist and show dataset inventory."""
    print("=" * 55)
    print("STEP 1 — FILE CHECK")
    print("=" * 55)

    def mark(path: Path) -> str:
        if not path.is_file():
            return f"❌ {path.name} — missing"
        return f"✅ {path.name} — exists"

    ml_dir = BACKEND_DIR / "ml_models"
    model_h5 = ml_dir / "lstm_price_predictor.h5"
    scaler_pkl = ml_dir / "scaler.pkl"

    print(mark(model_h5))
    print(mark(scaler_pkl))

    ds_dir = BACKEND_DIR / "datasets"
    print("\nDatasets (files in datasets/):")
    if not ds_dir.is_dir():
        print("❌ datasets/ folder missing")
    else:
        any_file = False
        for p in sorted(ds_dir.iterdir()):
            if p.is_file():
                any_file = True
                if p.suffix.lower() == ".csv":
                    rows = _count_csv_rows(p)
                    print(f"  ✅ {p.name} — {rows:,} rows")
                else:
                    print(f"  ✅ {p.name} — (non-CSV, row count skipped)")
        if not any_file:
            print("  ❌ folder is empty")

    env_path = BACKEND_DIR / ".env"
    print("\n.env:")
    if not env_path.is_file():
        print("❌ .env — missing")
    else:
        print("✅ .env — exists")
        for key in ("NEWS_API_KEY", "MONGO_URI", "WEATHER_API_KEY"):
            set_now = bool(os.getenv(key))
            print(f"  {key}: {'set' if set_now else 'missing / empty'}")

    services = BACKEND_DIR / "app" / "services"
    checks = [
        (services / "weather_service.py", "Open-Meteo"),
        (services / "news_service.py", "NewsAPI"),
        (services / "lstm_service.py", "LSTM pipeline"),
        (services / "preprocessing_service.py", "windows"),
    ]
    print("\napp/services:")
    for path, label in checks:
        if not path.is_file():
            print(f"❌ {path.name} — missing ({label})")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        placeholder = "placeholder" in text.lower() and "news_service" in path.name
        if path.name == "news_service.py" and "newsapi.org" in text.lower():
            placeholder = False
        if path.name == "weather_service.py" and "open-meteo" in text.lower():
            placeholder = False
        if placeholder:
            print(f"⚠️ {path.name} — still looks like placeholder")
        else:
            print(f"✅ {path.name} — real code ({label})")


def main() -> None:
    step1_file_audit()

    # Test result flags for summary
    flags = {
        "weather_api": False,
        "news_api": False,
        "mongo": False,
        "model": False,
        "prediction": False,
        "weather_service": "❌",
        "news_service": "❌",
    }

    print("\n" + "=" * 55)
    print("STEP 2 — CONNECTION & SERVICE TESTS")
    print("=" * 55)

    # TEST 1 — Open-Meteo direct
    print("\n--- TEST 1: Weather API (raw Open-Meteo) ---")
    try:
        import requests

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": 6.9708,
            "longitude": 80.7736,
            "daily": "precipitation_sum",
            "timezone": "Asia/Colombo",
            "forecast_days": 7,
        }
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        data = r.json()
        rains = data.get("daily", {}).get("precipitation_sum", [])
        dates = data.get("daily", {}).get("time", [])
        print("Rainfall next days (mm):", rains)
        print("Dates:", dates)
        print("WEATHER ✅")
        flags["weather_api"] = True
    except Exception as exc:  # noqa: BLE001
        print(f"WEATHER ❌ {exc}")

    # TEST 2 — NewsAPI direct
    print("\n--- TEST 2: News API (raw NewsAPI.org) ---")
    key = os.getenv("NEWS_API_KEY", "").strip()
    if not key:
        print("NEWS ❌ NEWS_API_KEY is not set in environment (.env)")
    else:
        try:
            import requests

            nr = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": "tomato price Sri Lanka",
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 3,
                },
                headers={"X-Api-Key": key},
                timeout=8,
            )
            body = nr.json()
            if nr.status_code != 200:
                print(f"NEWS ❌ HTTP {nr.status_code}: {body.get('message', body)}")
            else:
                arts = body.get("articles") or []
                for i, a in enumerate(arts[:3], 1):
                    print(f"  {i}. {a.get('title', '')[:120]}")
                print("NEWS ✅")
                flags["news_api"] = True
        except Exception as exc:  # noqa: BLE001
            print(f"NEWS ❌ {exc}")

    # TEST 3 — MongoDB
    print("\n--- TEST 3: MongoDB ---")
    uri = os.getenv("MONGO_URI", "").strip()
    if not uri:
        print("MONGODB ❌ MONGO_URI is not set")
    else:
        try:
            from pymongo import MongoClient

            client = MongoClient(uri, serverSelectionTimeoutMS=8000)
            client.admin.command("ping")
            print("MONGODB ✅ ping OK")
            flags["mongo"] = True
            client.close()
        except Exception as exc:  # noqa: BLE001
            print(f"MONGODB ❌ {exc}")

    # TEST 4 — LSTM files
    print("\n--- TEST 4: LSTM model files ---")
    model_path = BACKEND_DIR / "ml_models" / "lstm_price_predictor.h5"
    scaler_path = BACKEND_DIR / "ml_models" / "scaler.pkl"
    if not model_path.is_file() or not scaler_path.is_file():
        print("MODEL ❌ model or scaler file missing — run: python train_model.py")
    else:
        try:
            import pickle
            from tensorflow.keras.models import load_model

            m = load_model(model_path)
            print("MODEL input shape:", m.input_shape)
            with open(scaler_path, "rb") as sf:
                scaler = pickle.load(sf)
            # MinMaxScaler exposes data_min_/data_max_ after fitting
            mn = float(getattr(scaler, "data_min_", [0.0])[0])
            mx = float(getattr(scaler, "data_max_", [0.0])[0])
            print(f"Scaler fitted price range (training min/max): {mn:.2f} → {mx:.2f}")
            print("MODEL ✅")
            flags["model"] = True
        except Exception as exc:  # noqa: BLE001
            print(f"MODEL ❌ {exc}")

    # TEST 5 — Full prediction (past_prices omitted → loaded from datasets CSV)
    print("\n--- TEST 5: Full prediction ---")
    if not flags["model"]:
        print("PREDICTION ❌ skipped (model not loaded)")
    else:
        try:
            from app.schemas.prediction_schema import PricePredictionRequest
            from app.services.lstm_service import generate_price_prediction

            req = PricePredictionRequest(
                location="Dambulla",
                forecast_horizon_days=7,
                currency="LKR/kg",
                window_size=10,
            )
            out = generate_price_prediction(req)
            print("First forecast day (LKR):", out.predicted_prices[0] if out.predicted_prices else "n/a")
            print("PREDICTION ✅")
            flags["prediction"] = True
        except Exception as exc:  # noqa: BLE001
            print(f"PREDICTION ❌ {exc}")

    # TEST 6 — Weather service wrapper
    print("\n--- TEST 6: weather_service.fetch_weather_signal ---")
    try:
        from app.services.weather_service import fetch_weather_signal

        w = fetch_weather_signal("Nuwara Eliya")
        print("Signal:", w.weather_signal)
        print("Temperature °C:", w.expected_temperature_celsius)
        print("Daily rain mm:", w.daily_rainfall)
        print("data_source:", w.data_source)
        if w.data_source == "Open-Meteo API":
            print("WEATHER SERVICE ✅")
            flags["weather_service"] = "✅"
        else:
            print("WEATHER SERVICE ⚠️ using fallback")
            flags["weather_service"] = "⚠️"
    except Exception as exc:  # noqa: BLE001
        print(f"WEATHER SERVICE ❌ {exc}")
        flags["weather_service"] = "❌"

    # TEST 7 — News service wrapper
    print("\n--- TEST 7: news_service.analyze_market_news ---")
    try:
        from app.services.news_service import analyze_market_news

        n = analyze_market_news("tomato Sri Lanka")
        print("Sentiment:", n.sentiment)
        print("Headlines sample:", getattr(n, "headlines", [])[:3])
        ds = getattr(n, "data_source", "")
        print("data_source:", ds)
        if ds == "NewsAPI.org":
            print("NEWS SERVICE ✅")
            flags["news_service"] = "✅"
        elif ds == "NewsAPI.org (no results)":
            print("NEWS SERVICE ✅ (API OK, zero articles — neutral response)")
            flags["news_service"] = "✅"
        elif ds == "fallback":
            print("NEWS SERVICE ⚠️ using fallback")
            flags["news_service"] = "⚠️"
        else:
            print("NEWS SERVICE ⚠️ unknown source")
            flags["news_service"] = "⚠️"
    except Exception as exc:  # noqa: BLE001
        print(f"NEWS SERVICE ❌ {exc}")
        flags["news_service"] = "❌"

    print("\n" + "=" * 55)
    print("SYSTEM STATUS SUMMARY")
    print("=" * 55)
    print(f"Weather API      : {'✅' if flags['weather_api'] else '❌'}")
    print(f"News API         : {'✅' if flags['news_api'] else '❌'}")
    print(f"MongoDB          : {'✅' if flags['mongo'] else '❌'}")
    print(f"LSTM Model       : {'✅' if flags['model'] else '❌'}")
    print(f"Prediction       : {'✅' if flags['prediction'] else '❌'}")
    print(f"Weather Service  : {flags['weather_service']}")
    print(f"News Service     : {flags['news_service']}")
    print("=" * 55)
    ready = all(
        [
            flags["weather_api"],
            flags["mongo"],
            flags["model"],
            flags["prediction"],
        ]
    ) and flags["news_api"] and flags["weather_service"] == "✅" and flags["news_service"] == "✅"
    print("Overall:", "READY" if ready else "NEEDS FIXES")
    print("=" * 55)
    print("\nStart API with: uvicorn main:app --reload --port 8000")


if __name__ == "__main__":
    main()
