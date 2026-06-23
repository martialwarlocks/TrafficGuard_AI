"""Secondary visual verification of ML violation classifications (backend-only)."""

import logging

from backend.app.config import get_settings
from backend.app.services.gemini_client import generate_json, parse_json_response
from backend.app.services.routing import RoutingEngine
from ml.pipeline.summary import generate_user_summary
from ml.violations.catalog import FRIENDLY_VIOLATION_LABELS, VIOLATION_CATALOG

logger = logging.getLogger(__name__)

VALID_TYPES = {v["id"] for v in VIOLATION_CATALOG} | {"none"}


def _current_violation_type(result: dict) -> str | None:
    primary = result.get("primary_violation")
    if primary:
        return primary.get("violation_type")
    summary = result.get("user_summary") or {}
    return summary.get("inferred_violation_type")


def _build_prompt(ml_type: str | None, result: dict) -> str:
    detections = result.get("detections", [])
    det_summary = ", ".join(
        f"{d.get('class_name')}({d.get('confidence', 0):.0%})"
        for d in detections[:8]
    ) or "none"
    signal = result.get("traffic_signal") or {}
    ml_label = FRIENDLY_VIOLATION_LABELS.get(ml_type or "", ml_type or "none")

    return f"""You are a traffic enforcement vision expert. Review this traffic camera image.

Our computer vision pipeline predicted:
- Violation: {ml_label or "none / no violation"}
- ML confidence: {result.get("confidence", 0):.0%}
- Uncertainty: {result.get("uncertainty", 0):.0%}
- Traffic signal state: {signal.get("state", "unknown")} ({signal.get("confidence", 0):.0%})
- Objects detected: {det_summary}

Valid violation_type values (use exactly one):
red_light, stop_line, helmet, seatbelt, triple_riding, wrong_side, parking, none

Rules:
- red_light ONLY if a vehicle is clearly crossing during a RED signal
- helmet ONLY if a motorcycle rider has no helmet visible
- seatbelt ONLY if a car occupant clearly has no seatbelt
- If image is unclear or no violation is visible, use "none"
- Do NOT guess — prefer "none" over a weak violation

Respond with JSON only:
{{
  "agrees_with_ml": true or false,
  "violation_type": "<one of the valid types>",
  "confidence": 0.0 to 1.0,
  "brief_reason": "<one sentence>"
}}"""


def _parse_json_response(text: str) -> dict | None:
    return parse_json_response(text)


def verify_with_vision(image_bytes: bytes, result: dict) -> dict | None:
    """Call vision model to verify ML classification. Returns parsed verdict or None."""
    settings = get_settings()
    api_key = settings.gemini_api_key
    if not api_key or not settings.gemini_verify_enabled:
        return None

    ml_type = _current_violation_type(result)
    prompt = _build_prompt(ml_type, result)
    parsed = generate_json(api_key, prompt, image_bytes, temperature=0.1)
    if not parsed:
        logger.warning("Vision verification returned unparseable response")
        return None
    vtype = str(parsed.get("violation_type", "none")).strip().lower()
    if vtype not in VALID_TYPES:
        vtype = "none"
    parsed["violation_type"] = None if vtype == "none" else vtype
    return parsed


def apply_verification(result: dict, verdict: dict) -> dict:
    """Adjust ML result when visual verification disagrees. No vendor names exposed."""
    ml_type = _current_violation_type(result)
    verified_type = verdict.get("violation_type")
    agrees = verdict.get("agrees_with_ml", True)
    verified_conf = float(verdict.get("confidence", result.get("confidence", 0.5)))
    reason = verdict.get("brief_reason", "")

    if agrees:
        return result

    explanations = result.get("explanation", {})
    reasons = list(explanations.get("reasons", []))

    if verified_type is None:
        result["primary_violation"] = None
        result["violations"] = []
        new_conf = min(result.get("confidence", 0.5), 0.55)
        new_uncertainty = max(result.get("uncertainty", 0.2), 0.35)
        reasons.append(
            reason or "Independent visual review found no enforceable violation in this image."
        )
    else:
        label = FRIENDLY_VIOLATION_LABELS.get(verified_type, verified_type)
        result["primary_violation"] = {
            "violation_type": verified_type,
            "detected": True,
            "confidence": round(verified_conf, 4),
            "uncertainty": result.get("uncertainty", 0.15),
            "explanation": {
                "confidence": round(verified_conf, 4),
                "reasons": [reason or f"Visual review confirmed {label.lower()}."],
            },
            "evidence": result.get("primary_violation", {}).get("evidence", {}),
        }
        result["violations"] = [
            v for v in result.get("violations", [])
            if v.get("violation_type") != verified_type
        ]
        result["violations"].insert(0, result["primary_violation"])
        new_conf = verified_conf
        new_uncertainty = max(0.08, 1.0 - verified_conf)
        reasons.append(reason or f"Visual review confirmed {label.lower()}.")

    result["confidence"] = round(new_conf, 4)
    result["uncertainty"] = round(new_uncertainty, 4)
    explanations["reasons"] = reasons[:6]
    result["explanation"] = explanations

    router = RoutingEngine()
    routing_decision, routing_rationale = router.route(
        new_conf, new_uncertainty, reasons
    )
    result["routing_decision"] = routing_decision.value
    result["routing_rationale"] = routing_rationale

    result["user_summary"] = generate_user_summary(
        result.get("detections", []),
        result.get("ocr_result", {}),
        new_conf,
        new_uncertainty,
        routing_decision.value,
        routing_rationale,
        result.get("primary_violation"),
        explanations,
        result.get("scene_context"),
        result.get("traffic_signal"),
    )
    return result


def verify_and_correct(image_bytes: bytes, result: dict) -> dict:
    """Run verification and apply corrections if needed."""
    verdict = verify_with_vision(image_bytes, result)
    if not verdict:
        return result
    return apply_verification(result, verdict)
