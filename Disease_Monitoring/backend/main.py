from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import location_router, observation_router

app = FastAPI(
    title="Observation-Based Disease Recovery Monitoring",
    description=(
        "Repeated observation monitoring for tomato leaf and fruit with relative "
        "pseudo-severity, visual consistency checks, and trend analysis."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(observation_router.router, tags=["Observation Monitoring"])
app.include_router(location_router.router, tags=["Location"])


@app.get("/")
def root():
    return {
        "status": "Observation-Based Disease Recovery Monitoring",
        "supported_crop_parts": ["LEAF", "FRUIT"],
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
