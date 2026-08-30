from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class CreateCaseRequest(BaseModel):
    crop_part: str = Field(..., description="LEAF or FRUIT")
    label: Optional[str] = None


class CaseResponse(BaseModel):
    case_id: str
    crop_part: str
    label: Optional[str] = None
    created_at: str


class ObservationResponse(BaseModel):
    observation_id: str
    case_id: str
    crop_part: str
    created_at: str
    disease: str
    severity_score: float
    severity_class: str
    estimated_affected_area_percentage: Optional[float] = None
    similarity_score: Optional[float] = None
    consistency_status: str
    weather_context: Optional[Dict[str, Any]] = None
    trend: Optional[str] = None
    status: Optional[str] = None
    recommendation: Optional[Dict[str, Any]] = None
    accepted: bool = True
    image_path: Optional[str] = None
    location: Optional[Dict[str, Any]] = None


class UploadObservationResponse(BaseModel):
    accepted: bool
    case_id: str
    crop_part: str
    image_valid: bool
    gate_confidence: Optional[float] = None
    rejection_reason: Optional[str] = None
    similarity_score: Optional[float] = None
    consistency_status: Optional[str] = None
    disease: Optional[str] = None
    observation: Optional[ObservationResponse] = None
    overall_status: Optional[Dict[str, Any]] = None


class ObservationsListResponse(BaseModel):
    case_id: str
    crop_part: str
    observations: List[ObservationResponse]


class CaseStatusResponse(BaseModel):
    case_id: str
    crop_part: str
    observation_count: int
    overall_status: str
    monitoring_summary: Optional[Dict[str, Any]] = None
    farmer_insight: Optional[Dict[str, Any]] = None
    latest_observation: Optional[ObservationResponse] = None
    latest_recommendation: Optional[Dict[str, Any]] = None
    observations_summary: List[Dict[str, Any]] = []


class ImageQualityCheckResponse(BaseModel):
    ok: bool
    checks: Dict[str, Any]
    overall: str
    farmer_summary: str
    can_upload: bool = True


class FarmerInsightResponse(BaseModel):
    case_id: str
    available: bool
    title: str
    text: str
    disclaimer: Optional[str] = None
    source: Optional[str] = None
