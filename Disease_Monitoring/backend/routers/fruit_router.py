from fastapi import APIRouter, UploadFile, File, Form
from schemas.fruit_schema import FruitUploadResponse
from services import fruit_service

router = APIRouter()

@router.post("/upload", response_model=FruitUploadResponse)
async def upload_fruit(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...)
):
    return await fruit_service.process_upload(
        file, session_id, latitude, longitude
    )