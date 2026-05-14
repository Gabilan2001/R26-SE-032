from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.schemas.history_schema import HistoryRecord, HistoryResponse
from app.utils.db_utils import save_history_record, load_history_records

router = APIRouter()


@router.post("/", response_model=HistoryResponse)
def save_history(record: HistoryRecord):
    """Store a prediction or recommendation event in prediction history."""
    try:
        record.timestamp = datetime.utcnow()
        saved_id = save_history_record(record)
        return HistoryResponse(success=True, record_id=str(saved_id))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/", response_model=list[HistoryRecord])
def get_history(limit: int = 20):
    """Retrieve recent prediction history records."""
    try:
        return load_history_records(limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
