from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.database.connection import init_db
from app.routes.predict_routes import router as predict_router
from app.routes.weather_routes import router as weather_router
from app.routes.news_routes import router as news_router
from app.routes.recommendation_routes import router as recommendation_router
from app.routes.history_routes import router as history_router
from app.routes.stats_routes import router as stats_router

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

init_db()

app.include_router(predict_router, prefix="/predict", tags=["Prediction"])
app.include_router(weather_router, prefix="/weather", tags=["Weather"])
app.include_router(news_router, prefix="/news", tags=["News"])
app.include_router(recommendation_router, prefix="/recommendation", tags=["Recommendation"])
app.include_router(history_router, prefix="/history", tags=["History"])
app.include_router(stats_router, prefix="/stats", tags=["Statistics"])


@app.get("/", summary="Service status")
def root():
    return {
        "service": "Tomato Price Prediction",
        "status": "running",
        "version": settings.app_version,
        "endpoints": {
            "prediction": "/predict",
            "weather": "/weather",
            "news": "/news",
            "recommendation": "/recommendation",
            "history": "/history",
            "statistics": "/stats",
        },
    }
