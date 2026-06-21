from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database import get_db
from backend.app.models import Camera, Evidence, User
from backend.app.schemas import CameraCreate, CameraResponse, EvidenceResponse, FeedbackCreate
from backend.app.models import Feedback
from backend.app.auth import get_current_user, require_roles
from backend.app.services.storage import storage_service
from backend.app.services.audit import log_audit

router = APIRouter(tags=["Cameras & Evidence"])


@router.get("/cameras", response_model=list[CameraResponse])
async def list_cameras(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Camera).where(Camera.is_active == True))
    return result.scalars().all()


@router.post("/cameras", response_model=CameraResponse)
async def create_camera(
    camera_data: CameraCreate,
    current_user: User = Depends(require_roles("Admin", "Supervisor")),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Camera).where(Camera.camera_id == camera_data.camera_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Camera ID already exists")

    camera = Camera(**camera_data.model_dump())
    db.add(camera)
    await log_audit(db, "camera.create", user_id=current_user.id, resource_id=camera_data.camera_id)
    await db.flush()
    return camera


@router.get("/evidence/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    integrity = storage_service.verify_integrity(evidence.original_image_path, evidence.evidence_hash)
    evidence.integrity_status = "verified" if integrity else "compromised"
    return evidence


@router.post("/feedback")
async def submit_feedback(
    feedback_data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    feedback = Feedback(
        violation_id=feedback_data.violation_id,
        user_id=current_user.id,
        is_correct=feedback_data.is_correct,
        corrected_label=feedback_data.corrected_label,
        notes=feedback_data.notes,
    )
    db.add(feedback)
    await log_audit(db, "feedback.submit", user_id=current_user.id, resource_id=str(feedback_data.violation_id))
    await db.flush()
    return {"message": "Feedback recorded for continuous learning", "id": feedback.id}
