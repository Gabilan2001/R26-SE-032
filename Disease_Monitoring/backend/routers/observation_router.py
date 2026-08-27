from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile

from observation import observation_service as svc
from schemas.observation_schema import (
    CaseResponse,
    CaseStatusResponse,
    CreateCaseRequest,
    ObservationsListResponse,
    UploadObservationResponse,
)

router = APIRouter()


@router.post("/cases", response_model=CaseResponse)
async def create_case(body: CreateCaseRequest):
    return await svc.create_monitoring_case(body.crop_part, body.label)


@router.get("/cases/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str):
    return await svc.get_monitoring_case(case_id)


@router.post("/cases/{case_id}/observations", response_model=UploadObservationResponse)
async def upload_observation(
    case_id: str,
    file: UploadFile = File(...),
    crop_part: str = Form(...),
    disease: str = Form(...),
    latitude: Optional[float] = Form(default=None),
    longitude: Optional[float] = Form(default=None),
    confirm_same_case: bool = Form(default=False),
):
    return await svc.process_observation_upload(
        case_id=case_id,
        file=file,
        crop_part=crop_part,
        disease=disease,
        latitude=latitude,
        longitude=longitude,
        confirm_same_case=confirm_same_case,
    )


@router.get("/cases/{case_id}/observations", response_model=ObservationsListResponse)
async def list_observations(case_id: str):
    return await svc.list_observations(case_id)


@router.get("/cases/{case_id}/status", response_model=CaseStatusResponse)
async def case_status(case_id: str):
    return await svc.get_case_status(case_id)
