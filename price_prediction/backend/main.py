from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config.locations import list_known_location_labels
from app.config.settings import settings
from app.routes.predict_routes import router as predict_router
from app.routes.weather_routes import router as weather_router
from app.routes.news_routes import router as news_router
from app.routes.recommendation_routes import router as recommendation_router
from app.routes.history_routes import router as history_router
from app.routes.stats_routes import router as stats_router
from app.routes.data_routes import router as data_router
from app.routes.seasonal_routes import router as seasonal_router

app = FastAPI(
    title="Tomato Price Prediction Service",
    description="AI-powered tomato price forecasting and market recommendations for farmers.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(predict_router, prefix="/predict", tags=["Prediction"])
app.include_router(weather_router, prefix="/weather", tags=["Weather"])
app.include_router(news_router, prefix="/news", tags=["News"])
app.include_router(recommendation_router, prefix="/recommendation", tags=["Recommendation"])
app.include_router(history_router, prefix="/history", tags=["History"])
app.include_router(stats_router, prefix="/stats", tags=["Statistics"])
app.include_router(data_router, prefix="/prices", tags=["Data Updates"])
app.include_router(seasonal_router, prefix="/seasonal-forecast", tags=["Seasonal Forecast"])


# Local dashboard (HTML/JS) next to backend/ — open http://127.0.0.1:8000/ui/
_FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if _FRONTEND_DIR.is_dir():
    app.mount(
        "/ui",
        StaticFiles(directory=str(_FRONTEND_DIR), html=True),
        name="dashboard",
    )


@app.get("/", summary="Service status")
def root():
    return {
        "service": "Tomato Price Prediction",
        "status": "running",
        "version": settings.app_version,
        "endpoints": {
            "dashboard": "/ui",
            "prediction": "/predict",
            "weather": "/weather",
            "news": "/news",
            "news_market_analysis": "/news/market-analysis",
            "recommendation": "/recommendation",
            "history": "/history",
            "statistics": "/stats",
            "known_locations": "/meta/locations",
        },
    }


@app.get("/meta/locations", summary="Dropdown labels for market / region")
def known_locations():
    """Curated location names that map to coordinates for weather and news context."""
    return {"locations": list_known_location_labels()}
