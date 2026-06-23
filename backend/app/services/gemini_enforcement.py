"""Gemini-powered primary enforcement: plate OCR, violation ID, Indian MV Act fines."""

import logging
import re
import time
from typing import Any

import cv2
import numpy as np

from backend.app.config import get_settings
from backend.app.models import RoutingDecision
from backend.app.services.gemini_client import generate_json
from backend.app.services.indian_fines import (
    VALID_VIOLATION_TYPES,
    build_fine_prompt_block,
    get_fine_for_violation,
)
from backend.app.services.routing import RoutingEngine
from ml.violations.catalog import FRIENDLY_VIOLATION_LABELS

logger = logging.getLogger(__name__)

PLATE_PATTERN = re.compile(
    r"^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$|"
    r"^[0-9]{2}BH[0-9]{4}[A-Z]{2}$|"
    r"^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$"
)


def _normalize_plate(raw: str | None) -> str | None:
    if not raw or str(raw).lower() in ("null", "none", "n/a", "unknown"):
        return None
    plate = re.sub(r"[^A-Za-z0-9]", "", str(raw).upper())
    if len(plate) < 6:
        return None
    if PLATE_PATTERN.match(plate):
        return plate
    if 8 <= len(plate) <= 10 and plate[:2].isalpha():
        return plate
    return None


def _build_prompt() -> str:
    fines = build_fine_prompt_block()
    return f"""You are an expert Indian traffic enforcement officer analysing a CCTV/traffic camera image.

Tasks:
1. Read the vehicle registration number (license plate) — Indian formats only (MH12AB1234, DL3CAD1234, KA01MN1234, 22BH1234AA). Read character by character from the plate image.
2. Identify the PRIMARY traffic violation for that vehicle — only if clearly visible.
3. Assign the correct fine under the Motor Vehicles Act, 1988 (India).

Allowed violation_type (exactly one, or "none"):
red_light, stop_line, helmet, seatbelt, triple_riding, wrong_side, parking, none

Indian penalty schedule (use ONLY these amounts):
{fines}

Accuracy rules:
- helmet: motorcycle/scooter rider with NO helmet on head (police stopping riders without helmet counts)
- seatbelt: car occupant with seatbelt clearly NOT fastened
- triple_riding: more than two persons on one two-wheeler
- red_light: vehicle crossing while signal is clearly RED
- stop_line: vehicle beyond white stop line or on zebra crossing — NOT merely parked on road
- If plate unreadable: plate_number null, plate_confidence below 0.5
- If no violation: violation_type = "none", fine_inr = 0
- NEVER guess plate digits — only report what you can read
- fine_inr MUST match the schedule for violation_type

JSON only:
{{
  "plate_number": "<plate or null>",
  "plate_confidence": 0.0-1.0,
  "vehicle_type": "car|motorcycle|truck|bus|auto|unknown",
  "violation_type": "<type>",
  "violation_confidence": 0.0-1.0,
  "fine_inr": <integer>,
  "legal_section": "<section>",
  "traffic_signal_state": "red|green|yellow|unknown",
  "brief_reason": "<what you see>",
  "observed_items": ["<visible objects>"]
}}"""


def _image_quality_score(image_bytes: bytes) -> float:
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return 0.3
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(min(1.0, cv2.Laplacian(gray, cv2.CV_64F).var() / 500.0))


def _clamp_fine(violation_type: str | None, gemini_fine: Any) -> float:
    official = get_fine_for_violation(violation_type)
    if not violation_type:
        return 0.0
    try:
        proposed = int(gemini_fine)
    except (TypeError, ValueError):
        proposed = int(official["fine_inr"])
    return float(official["fine_inr"] if proposed != int(official["fine_inr"]) else proposed)


def _build_result(parsed: dict, quality_score: float, elapsed_ms: float) -> dict:
    vtype_raw = str(parsed.get("violation_type", "none")).strip().lower()
    violation_type = None if vtype_raw in ("none", "", "null") else vtype_raw
    if violation_type and violation_type not in VALID_VIOLATION_TYPES:
        violation_type = None

    plate = _normalize_plate(parsed.get("plate_number"))
    plate_conf = float(parsed.get("plate_confidence", 0.0))
    v_conf = float(parsed.get("violation_confidence", 0.0))
    vehicle_type = str(parsed.get("vehicle_type", "unknown")).lower()
    reason = str(parsed.get("brief_reason", "")).strip()
    signal_state = str(parsed.get("traffic_signal_state", "unknown")).lower()
    observed = parsed.get("observed_items") or []

    fine_info = get_fine_for_violation(violation_type)
    fine_inr = _clamp_fine(violation_type, parsed.get("fine_inr"))
    legal_section = fine_info["legal_section"] or parsed.get("legal_section")

    if violation_type:
        confidence = (v_conf * 0.6 + plate_conf * 0.4) if plate else v_conf * 0.85
    else:
        confidence = 0.35

    confidence = round(min(0.98, max(0.1, confidence)), 4)
    uncertainty = round(max(0.05, 1.0 - confidence), 4)

    reasons = []
    if reason:
        reasons.append(reason)
    if plate:
        reasons.append(f"Registration plate: {plate}")
    elif violation_type:
        reasons.append("Plate not clearly readable — officer must verify before challan.")
    if fine_inr > 0 and legal_section:
        label = FRIENDLY_VIOLATION_LABELS.get(violation_type or "", violation_type)
        reasons.append(f"Proposed challan: ₹{fine_inr:.0f} for {label} ({legal_section}).")

    router = RoutingEngine()
    routing_decision, routing_rationale = router.route(confidence, uncertainty, reasons)

    if violation_type and fine_inr > 0:
        if not plate or plate_conf < 0.6:
            routing_decision = RoutingDecision.HUMAN_REVIEW
            routing_rationale = (
                f"Violation identified — verify plate before issuing ₹{fine_inr:.0f} challan."
            )
    elif not violation_type:
        routing_decision = RoutingDecision.DISCARD
        routing_rationale = "No enforceable violation identified."

    primary_violation = None
    violations = []
    if violation_type:
        primary_violation = {
            "violation_type": violation_type,
            "detected": True,
            "confidence": confidence,
            "uncertainty": uncertainty,
            "fine_inr": fine_inr,
            "legal_section": legal_section,
            "explanation": {"confidence": confidence, "reasons": reasons[:4]},
            "evidence": {"plate_number": plate, "vehicle_type": vehicle_type},
        }
        violations = [primary_violation]

    found_items = [
        {"label": str(item).replace("_", " ").title(), "count": 1, "confidence": round(v_conf, 2)}
        for item in observed[:8]
    ]

    vlabel = FRIENDLY_VIOLATION_LABELS.get(violation_type or "", "")
    if violation_type and plate and fine_inr > 0:
        headline = f"Challan: ₹{fine_inr:.0f} — {vlabel}"
        verdict = f"Plate {plate} · {vlabel} · Fine ₹{fine_inr:.0f} ({legal_section}). {reason}"
    elif violation_type:
        headline = vlabel or violation_type.replace("_", " ").title()
        verdict = f"{reason} Plate: {plate or 'not readable'}."
    else:
        headline = "No violation detected"
        verdict = reason or "No clear traffic violation in this image."

    return {
        "detections": [],
        "violations": violations,
        "primary_violation": primary_violation,
        "confidence": confidence,
        "uncertainty": uncertainty,
        "model_confidence": round(v_conf, 4),
        "stability_score": round(plate_conf, 4),
        "quality_metrics": {"quality_score": round(quality_score, 4)},
        "ocr_result": {
            "text": plate,
            "confidence": round(plate_conf, 4),
            "alternatives": [],
            "source": "vision_enforcement",
        },
        "explanation": {"confidence": confidence, "uncertainty": uncertainty, "reasons": reasons[:6]},
        "routing_decision": routing_decision.value,
        "routing_rationale": routing_rationale,
        "traffic_signal": {
            "state": signal_state,
            "confidence": round(v_conf, 4) if signal_state != "unknown" else 0.0,
        },
        "scene_context": {},
        "annotated_image": None,
        "enhanced_image": None,
        "processing_time_ms": round(elapsed_ms, 2),
        "fine_amount": fine_inr,
        "legal_section": legal_section,
        "analysis_engine": "vision_enforcement",
        "user_summary": {
            "headline": headline,
            "verdict": verdict,
            "next_step": {
                "auto_process": f"Challan ₹{fine_inr:.0f} ready for plate {plate}.",
                "human_review": "Officer should verify plate and violation before issuing challan.",
                "discard": "No challan recommended.",
            }.get(routing_decision.value, routing_rationale),
            "found_items": found_items,
            "plate_number": plate,
            "vehicle_type": vehicle_type if vehicle_type != "unknown" else None,
            "inferred_violation_type": violation_type,
            "violation_label": vlabel or None,
            "routing_decision": routing_decision.value,
            "signal_state": signal_state if signal_state != "unknown" else None,
            "fine_inr": fine_inr,
            "legal_section": legal_section,
        },
    }


def _read_plate_focused(image_bytes: bytes, api_key: str) -> tuple[str | None, float]:
    """Second pass focused only on license plate OCR."""
    prompt = """Read the Indian vehicle registration number (license plate) in this image.
Look at the front or rear plate. Indian formats: MH12AB1234, DL3CAD1234, KA01MN1234.
Read each character carefully. If unreadable, return null.

JSON only: {"plate_number": "<plate or null>", "plate_confidence": 0.0-1.0}"""
    parsed = generate_json(api_key, prompt, image_bytes, temperature=0.0)
    if not parsed:
        return None, 0.0
    plate = _normalize_plate(parsed.get("plate_number"))
    conf = float(parsed.get("plate_confidence", 0.0))
    return plate, conf


def analyze_with_gemini(image_bytes: bytes) -> dict | None:
    settings = get_settings()
    if not settings.gemini_api_key or not settings.gemini_primary_enabled:
        return None

    start = time.time()
    try:
        quality = _image_quality_score(image_bytes)
        parsed = generate_json(settings.gemini_api_key, _build_prompt(), image_bytes)
        if not parsed:
            logger.warning("Gemini enforcement: unparseable response")
            return None
        elapsed = (time.time() - start) * 1000
        logger.info(
            "Gemini enforcement: violation=%s plate=%s fine=%s",
            parsed.get("violation_type"),
            parsed.get("plate_number"),
            parsed.get("fine_inr"),
        )
        result = _build_result(parsed, quality, elapsed)

        # Focused plate pass if violation found but plate missing
        if result.get("primary_violation") and not result.get("ocr_result", {}).get("text"):
            plate, pconf = _read_plate_focused(image_bytes, settings.gemini_api_key)
            if plate:
                result["ocr_result"] = {"text": plate, "confidence": round(pconf, 4), "alternatives": [], "source": "plate_ocr"}
                result["user_summary"]["plate_number"] = plate
                fine = result.get("fine_amount", 0)
                vlabel = result["user_summary"].get("violation_label", "")
                if fine > 0:
                    result["user_summary"]["headline"] = f"Challan: ₹{fine:.0f} — {vlabel}"
                    result["user_summary"]["verdict"] = (
                        f"Plate {plate} · {vlabel} · Fine ₹{fine:.0f} ({result.get('legal_section', '')})."
                    )
                result["explanation"]["reasons"].insert(0, f"Registration plate: {plate}")

        return result
    except Exception as exc:
        logger.error("Gemini enforcement failed: %s", exc)
        return None
