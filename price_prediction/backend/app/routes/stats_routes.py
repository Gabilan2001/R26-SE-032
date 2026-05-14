from fastapi import APIRouter, HTTPException

from app.schemas.stats_schema import StatsResponse
from app.utils.db_utils import load_analytics

router = APIRouter()


@router.get("/", response_model=StatsResponse)
def get_statistics():
    """Return aggregated prediction and market analytics."""
    try:
        return load_analytics()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
