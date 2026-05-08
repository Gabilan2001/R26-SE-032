from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import leaf_router, fruit_router

app = FastAPI(
    title="Component 3 - Disease Treatment Efficacy Monitoring",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leaf_router.router, prefix="/leaf", tags=["Leaf"])
app.include_router(fruit_router.router, prefix="/fruit", tags=["Fruit"])

@app.get("/")
def root():
    return {"status": "Component 3 running"}

@app.get("/health")
def health():
    return {"status": "healthy"}