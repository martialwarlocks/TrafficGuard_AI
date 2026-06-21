from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from backend.app.models import (
    UserRole, ViolationType, RoutingDecision, ReviewAction, CameraStatus,
)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: datetime
    type: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    role: UserRole = UserRole.OFFICER


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    avatar_url: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class CameraCreate(BaseModel):
    name: str
    camera_id: str
    stream_url: Optional[str] = None
    stream_type: str = "rtsp"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None


class CameraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    camera_id: str
    stream_url: Optional[str]
    stream_type: str
    latitude: Optional[float]
    longitude: Optional[float]
    location_name: Optional[str]
    status: CameraStatus
    is_active: bool
    fps: float


class ExplainabilityResult(BaseModel):
    confidence: float
    uncertainty: float
    reasons: list[str]


class ViolationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    violation_type: ViolationType
    camera_id: Optional[int]
    vehicle_type: Optional[str]
    plate_number: Optional[str]
    confidence: float
    uncertainty: float
    routing_decision: RoutingDecision
    routing_rationale: Optional[str]
    explanation: Optional[dict]
    status: str
    latitude: Optional[float]
    longitude: Optional[float]
    fine_amount: float
    detected_at: datetime


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    violation_id: int
    original_image_path: str
    enhanced_image_path: Optional[str]
    annotated_image_path: Optional[str]
    ocr_result: Optional[str]
    ocr_confidence: Optional[float]
    ocr_alternatives: Optional[list]
    evidence_hash: str
    integrity_status: str
    quality_metrics: Optional[dict]
    detection_data: Optional[dict]
    chain_of_custody: Optional[list]
    created_at: datetime


class ReviewCreate(BaseModel):
    violation_id: int
    action: ReviewAction
    notes: Optional[str] = None
    review_duration_seconds: Optional[int] = None


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    violation_id: int
    officer_id: int
    action: ReviewAction
    notes: Optional[str]
    created_at: datetime


class FeedbackCreate(BaseModel):
    violation_id: int
    is_correct: bool
    corrected_label: Optional[str] = None
    notes: Optional[str] = None


class DashboardStats(BaseModel):
    total_violations: int
    auto_processed: int
    human_reviewed: int
    review_rate: float
    avg_confidence: float
    avg_uncertainty: float
    active_cameras: int
    today_revenue: float
    system_health: float
    pending_reviews: int


class AnalyticsResponse(BaseModel):
    hourly_trends: list[dict]
    daily_trends: list[dict]
    monthly_trends: list[dict]
    violation_categories: list[dict]
    confidence_distribution: list[dict]
    uncertainty_distribution: list[dict]
    officer_productivity: list[dict]
    review_accuracy: float
    model_drift: list[dict]


class HeatmapPoint(BaseModel):
    latitude: float
    longitude: float
    intensity: float
    violation_count: int


class ModelMetricsResponse(BaseModel):
    precision: float
    recall: float
    map50: float
    map50_95: float
    f1_score: float
    avg_confidence: float
    avg_uncertainty: float
    latency_ms: float
    fps: float
    gpu_utilization: float
    drift_alerts: list[dict]
    retraining_status: str


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    redis: str
    minio: str
    elasticsearch: str
    ml_pipeline: str
    timestamp: datetime


class AnalyzeResponse(BaseModel):
    violation_id: Optional[int]
    violation_type: Optional[str]
    confidence: float
    uncertainty: float
    routing_decision: RoutingDecision
    routing_rationale: Optional[str] = None
    explanation: ExplainabilityResult
    detections: list[dict]
    quality_score: float
    processing_time_ms: float
    user_summary: Optional[dict] = None
    image_urls: Optional[dict] = None
    ocr_result: Optional[dict] = None
    traffic_signal: Optional[dict] = None
    scene_context: Optional[dict] = None


class ViolationDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    violation_type: ViolationType
    camera_id: Optional[int]
    vehicle_type: Optional[str]
    plate_number: Optional[str]
    confidence: float
    uncertainty: float
    routing_decision: RoutingDecision
    routing_rationale: Optional[str]
    explanation: Optional[dict]
    status: str
    detected_at: datetime
    image_urls: dict = {}
    ocr_result: Optional[dict] = None
    detection_data: Optional[list] = None
