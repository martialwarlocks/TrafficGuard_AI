"""Apply Indian MV Act fines and user-facing summaries to any analysis result."""

from ml.violations.catalog import FRIENDLY_VIOLATION_LABELS, VIOLATION_PRIORITY
from backend.app.services.indian_fines import get_fine_for_violation
from ml.pipeline.summary import generate_user_summary, infer_from_detections


def _current_violation_type(result: dict) -> str | None:
    primary = result.get("primary_violation")
    if primary:
        return primary.get("violation_type")
    summary = result.get("user_summary") or {}
    if summary.get("inferred_violation_type"):
        return summary["inferred_violation_type"]
    inferred = infer_from_detections(
        result.get("detections", []),
        result.get("scene_context"),
        result.get("traffic_signal"),
    )
    return inferred.get("violation_type")


def enrich_with_fines(result: dict) -> dict:
    """Ensure plate, fine_inr, and user_summary are populated."""
    vtype = _current_violation_type(result)
    fine_info = get_fine_for_violation(vtype)
    fine_inr = fine_info["fine_inr"]
    legal_section = fine_info["legal_section"]

    ocr = result.get("ocr_result") or {}
    plate = ocr.get("text") or (result.get("user_summary") or {}).get("plate_number")

    if vtype and fine_inr > 0:
        result["fine_amount"] = fine_inr
        result["legal_section"] = legal_section
        primary = result.get("primary_violation")
        if primary:
            primary["fine_inr"] = fine_inr
            primary["legal_section"] = legal_section

    summary = result.get("user_summary")
    if not summary or not summary.get("fine_inr"):
        summary = generate_user_summary(
            result.get("detections", []),
            result.get("ocr_result", {}),
            result.get("confidence", 0.5),
            result.get("uncertainty", 0.3),
            result.get("routing_decision", "human_review"),
            result.get("routing_rationale", ""),
            result.get("primary_violation"),
            result.get("explanation", {}),
            result.get("scene_context"),
            result.get("traffic_signal"),
        )
        if vtype and fine_inr > 0:
            label = FRIENDLY_VIOLATION_LABELS.get(vtype, vtype)
            summary["fine_inr"] = fine_inr
            summary["legal_section"] = legal_section
            if plate:
                summary["headline"] = f"Challan: ₹{fine_inr:.0f} — {label}"
                summary["verdict"] = (
                    f"Vehicle {plate} — {label}. Fine ₹{fine_inr:.0f} under {legal_section}."
                )
        result["user_summary"] = summary

    return result


def fix_violation_priority(result: dict) -> dict:
    """Prefer explicit ML detections (no_helmet) over heuristic stop_line."""
    detections = result.get("detections", [])
    classes = {d.get("class_name") for d in detections}
    violations = result.get("violations") or []

    if not violations:
        return result

    suppress = set()
    if "no_helmet" in classes:
        suppress.update({"stop_line", "seatbelt", "parking"})
    if "no_seatbelt" in classes:
        suppress.update({"stop_line", "parking"})
    if "helmet" in classes and "motorcycle" in classes and "no_helmet" not in classes:
        suppress.add("helmet")

    if suppress:
        violations = [v for v in violations if v.get("violation_type") not in suppress]

    if violations:
        primary = None
        for vtype in VIOLATION_PRIORITY:
            for v in violations:
                if v.get("violation_type") == vtype:
                    primary = v
                    break
            if primary:
                break
        if not primary:
            primary = violations[0]
        result["violations"] = violations
        result["primary_violation"] = primary
    else:
        result["violations"] = []
        result["primary_violation"] = None

    return result
