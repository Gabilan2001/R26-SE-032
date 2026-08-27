from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from schemas.leaf_schema import LeafUploadResponse, TRRResponse
from services import leaf_service
from services.rag_engine import get_alternative_treatment
from utils.db_utils import get_all_uploaded_days, get_session_history

router = APIRouter()

@router.post("/upload", response_model=LeafUploadResponse)
async def upload_leaf(
    file:      UploadFile = File(...),
    session_id: str       = Form(...),
    day:        int       = Form(...),
    latitude:   float     = Form(...),
    longitude:  float     = Form(...),
):
    if day not in [1, 3, 7]:
        raise HTTPException(400, "Day must be 1, 3, or 7")

    return await leaf_service.process_upload(
        file, session_id, day, latitude, longitude
    )

@router.get("/trr/{session_id}", response_model=TRRResponse)
async def get_trr(
    session_id: str,
    failed_medicine: str = Query(default="Unknown"),
    failed_class: str = Query(default="Unknown"),
    disease_name: str = Query(default="Tomato_Disease"),
):
    result = await leaf_service.compute_trr_result(session_id)

    if result["overall_verdict"] == "FAILURE":
        history = get_session_history(session_id)
        day7_data = history.get("day7", {})
        weather = day7_data.get("weather", {})

        alternative = get_alternative_treatment(
            failed_medicine=failed_medicine,
            failed_class=failed_class,
            disease_name=disease_name,
            weather=weather,
        )
        result["alternative_treatment"] = alternative
        result["rag_triggered"]         = True
        result["failed_medicine"]       = failed_medicine
        result["failed_class"]          = failed_class
        result["disease_name"]          = disease_name
    else:
        result["alternative_treatment"] = None
        result["rag_triggered"]         = False
        result["failed_medicine"]       = None
        result["failed_class"]          = None
        result["disease_name"]          = None

    return result

@router.get("/status/{session_id}")
async def get_status(session_id: str):
    uploaded_days = get_all_uploaded_days(session_id)

    return {
        "session_id":     session_id,
        "days_uploaded":  uploaded_days,
        "days_remaining": [d for d in [1, 3, 7] if d not in uploaded_days],
        "ready_for_trr":  7 in uploaded_days,
    }