import base64
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
from backend.app.services.analysis import store_analysis_images, image_urls_for_evidence, encode_image_b64
from backend.app.services.ml_service import get_analyzer
from backend.app.services.gemini_enforcement import analyze_with_gemini
from backend.app.services.enforcement_enricher import enrich_with_fines, fix_violation_priority
from backend.app.services.classification_verifier import verify_and_correct
from backend.app.services.audit import log_audit
from ml.pipeline.summary import infer_from_detections

router = APIRouter(tags=["Violations"])


def _run_yolo_analysis(content: bytes, camera_id: int | None = None) -> dict:
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    try:
        analyzer = get_analyzer()
        result = analyzer.analyze(tmp_path, camera_id=camera_id)
        result = fix_violation_priority(result)
        return result
    finally:
        os.unlink(tmp_path)


def _merge_gemini_with_yolo(gemini: dict, yolo: dict) -> dict:
    """Gemini decision + YOLO bounding-box annotations for display."""
    if yolo.get("annotated_image") is not None:
        gemini["annotated_image"] = yolo["annotated_image"]
    if yolo.get("enhanced_image") is not None:
        gemini["enhanced_image"] = yolo["enhanced_image"]
    if yolo.get("detections"):
        gemini["detections"] = yolo["detections"]
        # Merge found_items from YOLO if Gemini list is sparse
        if len(gemini.get("user_summary", {}).get("found_items", [])) < 2:
            yolo_summary = yolo.get("user_summary", {})
            if yolo_summary.get("found_items"):
                gemini["user_summary"]["found_items"] = yolo_summary["found_items"]
    return gemini


def _run_analysis(content: bytes, camera_id: int | None = None) -> dict:
    from backend.app.config import get_settings
    settings = get_settings()

    yolo_result = None
    try:
        yolo_result = _run_yolo_analysis(content, camera_id)
    except Exception:
        yolo_result = None

    if settings.gemini_api_key and settings.gemini_primary_enabled:
        gemini_result = analyze_with_gemini(content)
        if gemini_result:
            if yolo_result:
                gemini_result = _merge_gemini_with_yolo(gemini_result, yolo_result)
            return gemini_result

    if yolo_result:
        if settings.gemini_verify_enabled:
            yolo_result = verify_and_correct(content, yolo_result)
        return enrich_with_fines(fix_violation_priority(yolo_result))

    raise HTTPException(status_code=503, detail="Analysis unavailable — check ML pipeline and Gemini API key")


@router.post("/upload")
async def upload_media(
    file: UploadFile = File(...),
    camera_id: int | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    result = _run_analysis(content, camera_id)
    images = store_analysis_images(content, result)
    violation_record = await _save_violation(db, result, camera_id, images)
    await log_audit(db, "violation.upload", user_id=current_user.id, resource_id=str(violation_record.id))
    return {"violation_id": violation_record.id, "analysis": _public_result(result, images)}


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(
    file: UploadFile = File(...),
    camera_id: int | None = Form(None),
    live_mode: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    result = _run_analysis(content, camera_id)

    violation_id = None
    image_urls = {}
    annotated_b64 = None

    if result.get("annotated_image") is not None:
        annotated_b64 = encode_image_b64(
            cv2.imencode(".jpg", result["annotated_image"])[1].tobytes()
        )

    # Live mode: only persist when a violation is detected (saves storage + DB noise)
    should_save = _should_persist(result)
    if live_mode:
        should_save = should_save and (
            result.get("primary_violation") is not None
            or result["routing_decision"] in ("auto_process", "human_review")
        )

    if should_save and not live_mode:
        images = store_analysis_images(content, result)
        violation = await _save_violation(db, result, camera_id, images)
        violation_id = violation.id
        await log_audit(db, "violation.analyze", user_id=current_user.id, resource_id=str(violation_id))
        image_urls = {
            "original": images.get("original_url"),
            "enhanced": images.get("enhanced_url"),
            "annotated": images.get("annotated_url"),
        }
    elif should_save and live_mode and result.get("primary_violation"):
        images = store_analysis_images(content, result)
        violation = await _save_violation(db, result, camera_id, images)
        violation_id = violation.id
        await log_audit(db, "violation.live_capture", user_id=current_user.id, resource_id=str(violation_id))
        image_urls = {"annotated": images.get("annotated_url")}

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
        image_urls=image_urls or None,
        annotated_image_b64=annotated_b64,
        ocr_result=result.get("ocr_result"),
        traffic_signal=result.get("traffic_signal"),
        scene_context=result.get("scene_context"),
        fine_amount=float(result.get("fine_amount") or summary.get("fine_inr") or 0.0),
        legal_section=result.get("legal_section") or summary.get("legal_section"),
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

    explanation = dict(result.get("explanation") or {})
    if result.get("legal_section"):
        explanation["legal_section"] = result["legal_section"]

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
        explanation=explanation,
        status=status,
        fine_amount=float(result.get("fine_amount") or summary.get("fine_inr") or 0.0),
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
    clean = {k: v for k, v in result.items() if k not in ("annotated_image", "enhanced_image")}
    clean["image_urls"] = {
        "original": images.get("original_url"),
        "enhanced": images.get("enhanced_url"),
        "annotated": images.get("annotated_url"),
    }
    return clean
