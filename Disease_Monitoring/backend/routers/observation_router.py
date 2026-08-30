from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import Response

from observation import observation_service as svc
from utils.image_quality import analyze_image_quality
from schemas.observation_schema import (
    CaseResponse,
    CaseStatusResponse,
    CreateCaseRequest,
    FarmerInsightResponse,
    ImageQualityCheckResponse,
    ObservationsListResponse,
    UploadObservationResponse,
)

router = APIRouter()


@router.post("/observations/quality-check", response_model=ImageQualityCheckResponse)
async def quality_check(
    file: UploadFile = File(...),
    crop_part: str = Form(default="LEAF"),
):
    """Advisory blur / brightness / distance hints before upload (does not gate)."""
    data = await file.read()
    return analyze_image_quality(data, crop_part=crop_part.upper())


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
    area: Optional[str] = Form(default=None),
    district: Optional[str] = Form(default=None),
    province: Optional[str] = Form(default=None),
    location_label: Optional[str] = Form(default=None),
    location_source: Optional[str] = Form(default=None),
    confirm_same_case: bool = Form(default=False),
):
    return await svc.process_observation_upload(
        case_id=case_id,
        file=file,
        crop_part=crop_part,
        disease=disease,
        latitude=latitude,
        longitude=longitude,
        area=area,
        district=district,
        province=province,
        location_label=location_label,
        location_source=location_source,
        confirm_same_case=confirm_same_case,
    )


@router.get("/cases/{case_id}/observations", response_model=ObservationsListResponse)
async def list_observations(case_id: str):
    return await svc.list_observations(case_id)


@router.get("/cases/{case_id}/status", response_model=CaseStatusResponse)
async def case_status(case_id: str):
    return await svc.get_case_status(case_id)


@router.get("/cases/{case_id}/insight", response_model=FarmerInsightResponse)
async def case_insight(case_id: str):
    """Farmer-facing explanation of stored scores — does not recompute severity."""
    return await svc.get_farmer_insight(case_id)


@router.get("/cases/{case_id}/report.pdf")
async def case_report_pdf(case_id: str):
    """Downloadable monitoring PDF built from stored case facts."""
    pdf_bytes = await svc.build_case_report_pdf(case_id)
    filename = f"monitoring-report-{case_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
