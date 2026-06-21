import cv2
import numpy as np
import tempfile
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.database import get_db
from backend.app.models import Violation, Evidence, RoutingDecision, ViolationType, User
from backend.app.schemas import ViolationResponse, AnalyzeResponse, ExplainabilityResult, ViolationDetailResponse
from backend.app.auth import get_current_user
from backend.app.services.storage import storage_service
from backend.app.services.analysis import store_analysis_images, image_urls_for_evidence
from backend.app.services.audit import log_audit
from ml.pipeline.summary import infer_from_detections

router = APIRouter(tags=["Violations"])


@router.post("/upload")
async def upload_media(
    file: UploadFile = File(...),
    camera_id: int | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        from ml.pipeline.analyzer import TrafficAnalyzer
        analyzer = TrafficAnalyzer()
        result = analyzer.analyze(tmp_path, camera_id=camera_id)
    finally:
        os.unlink(tmp_path)

    images = store_analysis_images(content, result)
    violation_record = await _save_violation(db, result, camera_id, images)
    await log_audit(db, "violation.upload", user_id=current_user.id, resource_id=str(violation_record.id))

    return {
        "violation_id": violation_record.id,
        "analysis": _public_result(result, images),
    }


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(
    file: UploadFile = File(...),
    camera_id: int | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        from ml.pipeline.analyzer import TrafficAnalyzer
        analyzer = TrafficAnalyzer()
        result = analyzer.analyze(tmp_path, camera_id=camera_id)
    finally:
        os.unlink(tmp_path)

    images = store_analysis_images(content, result)
    violation_id = None
    should_persist = _should_persist(result)

    if should_persist:
        violation = await _save_violation(db, result, camera_id, images)
        violation_id = violation.id
        await log_audit(db, "violation.analyze", user_id=current_user.id, resource_id=str(violation_id))

    summary = result.get("user_summary", {})
    primary = result.get("primary_violation")
    violation_type = (
        primary.get("violation_type") if primary
        else summary.get("inferred_violation_type")
    )

    return AnalyzeResponse(
        violation_id=violation_id,
        violation_type=violation_type,
        confidence=result["confidence"],
        uncertainty=result["uncertainty"],
        routing_decision=RoutingDecision(result["routing_decision"]),
        routing_rationale=result["routing_rationale"],
        explanation=ExplainabilityResult(**result["explanation"]),
        detections=result["detections"],
        quality_score=result["quality_metrics"]["quality_score"],
        processing_time_ms=result["processing_time_ms"],
        user_summary=summary,
        image_urls={
            "original": images.get("original_url"),
            "enhanced": images.get("enhanced_url"),
            "annotated": images.get("annotated_url"),
        },
        ocr_result=result.get("ocr_result"),
        traffic_signal=result.get("traffic_signal"),
        scene_context=result.get("scene_context"),
    )


@router.get("/violations", response_model=list[ViolationResponse])
async def list_violations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    violation_type: str | None = None,
    routing_decision: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Violation).order_by(desc(Violation.detected_at)).offset(skip).limit(limit)
    if violation_type:
        query = query.where(Violation.violation_type == violation_type)
    if routing_decision:
        query = query.where(Violation.routing_decision == routing_decision)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/violations/{violation_id}", response_model=ViolationResponse)
async def get_violation(
    violation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Violation).where(Violation.id == violation_id))
    violation = result.scalar_one_or_none()
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")
    return violation


@router.get("/violations/{violation_id}/detail", response_model=ViolationDetailResponse)
async def get_violation_detail(
    violation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Violation).where(Violation.id == violation_id))
    violation = result.scalar_one_or_none()
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")

    ev_result = await db.execute(select(Evidence).where(Evidence.violation_id == violation_id))
    evidence = ev_result.scalar_one_or_none()

    image_urls = image_urls_for_evidence(evidence) if evidence else {}

    return ViolationDetailResponse(
        id=violation.id,
        violation_type=violation.violation_type,
        camera_id=violation.camera_id,
        vehicle_type=violation.vehicle_type,
        plate_number=violation.plate_number,
        confidence=violation.confidence,
        uncertainty=violation.uncertainty,
        routing_decision=violation.routing_decision,
        routing_rationale=violation.routing_rationale,
        explanation=violation.explanation,
        status=violation.status,
        detected_at=violation.detected_at,
        image_urls=image_urls,
        ocr_result={"text": evidence.ocr_result, "confidence": evidence.ocr_confidence} if evidence else None,
        detection_data=evidence.detection_data if evidence else None,
    )


def _should_persist(result: dict) -> bool:
    """Save analysis when there's anything actionable or reviewable."""
    if result.get("detections"):
        return True
    if result.get("primary_violation"):
        return True
    if result["routing_decision"] in ("human_review", "auto_process"):
        return True
    return False


async def _save_violation(db, result, camera_id, images: dict):
    primary = result.get("primary_violation")
    summary = result.get("user_summary", {})
    inferred = infer_from_detections(result.get("detections", []))

    vtype_str = (
        primary.get("violation_type") if primary
        else summary.get("inferred_violation_type") or inferred.get("violation_type") or "helmet"
    )
    try:
        vtype = ViolationType(vtype_str)
    except ValueError:
        vtype = ViolationType.HELMET

    routing = result["routing_decision"]
    status = "pending" if routing == "human_review" else routing

    violation = Violation(
        violation_type=vtype,
        camera_id=camera_id,
        vehicle_type=summary.get("vehicle_type") or inferred.get("vehicle_type"),
        plate_number=result.get("ocr_result", {}).get("text") or summary.get("plate_number"),
        confidence=result["confidence"],
        uncertainty=result["uncertainty"],
        model_confidence=result.get("model_confidence"),
        quality_score=result.get("quality_metrics", {}).get("quality_score"),
        stability_score=result.get("stability_score"),
        ocr_confidence=result.get("ocr_result", {}).get("confidence"),
        routing_decision=RoutingDecision(routing),
        routing_rationale=result["routing_rationale"],
        explanation=result["explanation"],
        status=status,
        detected_at=datetime.utcnow(),
    )
    db.add(violation)
    await db.flush()

    evidence = Evidence(
        violation_id=violation.id,
        original_image_path=images["original_path"],
        enhanced_image_path=images.get("enhanced_path"),
        annotated_image_path=images.get("annotated_path"),
        ocr_result=result.get("ocr_result", {}).get("text"),
        ocr_confidence=result.get("ocr_result", {}).get("confidence"),
        ocr_alternatives=result.get("ocr_result", {}).get("alternatives"),
        evidence_hash=images["evidence_hash"],
        quality_metrics=result.get("quality_metrics"),
        detection_data=result.get("detections"),
        chain_of_custody=[{
            "action": "captured",
            "timestamp": datetime.utcnow().isoformat(),
            "hash": images["evidence_hash"],
        }],
    )
    db.add(evidence)
    await db.flush()
    return violation


def _public_result(result: dict, images: dict) -> dict:
    """Strip numpy images from API payload."""
    clean = {k: v for k, v in result.items() if k not in ("annotated_image", "enhanced_image")}
    clean["image_urls"] = {
        "original": images.get("original_url"),
        "enhanced": images.get("enhanced_url"),
        "annotated": images.get("annotated_url"),
    }
    return clean
