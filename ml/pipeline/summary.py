"""Generate user-friendly analysis summaries."""

from ml.violations.catalog import FRIENDLY_VIOLATION_LABELS

FRIENDLY_NAMES = {
    "person": "Person",
    "car": "Car",
    "motorcycle": "Motorcycle",
    "bus": "Bus",
    "truck": "Truck",
    "bicycle": "Bicycle",
    "traffic_light_red": "Red traffic signal",
    "traffic_light_green": "Green traffic signal",
    "helmet": "Helmet (worn)",
    "no_helmet": "No helmet",
    "seatbelt": "Seatbelt (worn)",
    "no_seatbelt": "No seatbelt",
    "license_plate": "License plate",
}

ROUTING_MESSAGES = {
    "auto_process": "High confidence — this case can be auto-processed for enforcement.",
    "human_review": "Medium confidence — an officer should review this before any action is taken.",
    "discard": "Low confidence — not enough reliable evidence to act on this detection.",
}


def infer_from_detections(
    detections: list[dict],
    scene_context: dict | None = None,
    signal_state: dict | None = None,
) -> dict:
    """Infer violation type only from explicit evidence — never guess seatbelt from car+person."""
    classes = {d.get("class_name") for d in detections}
    vehicle = None
    if "motorcycle" in classes:
        vehicle = "motorcycle"
    elif "car" in classes:
        vehicle = "car"
    elif "truck" in classes:
        vehicle = "truck"
    elif "bus" in classes:
        vehicle = "bus"

    violation_type = None
    ctx = scene_context or {}
    sig = signal_state or {}

    # Priority 1: Signal violations — require crosswalk evidence
    if sig.get("state") in ("red", "yellow") and sig.get("confidence", 0) >= 0.45:
        if ctx.get("vehicles_in_crosswalk"):
            violation_type = "red_light"
        elif ctx.get("crosswalk_detected") and ctx.get("vehicles_past_stop_line"):
            violation_type = "red_light"
    elif ctx.get("vehicles_in_crosswalk") and ctx.get("crosswalk_detected"):
        violation_type = "stop_line"

    # Priority 2: Explicit detection classes only
    elif "no_helmet" in classes:
        violation_type = "helmet"
    elif "no_seatbelt" in classes:
        violation_type = "seatbelt"
    elif "helmet" in classes and vehicle == "motorcycle":
        violation_type = None  # compliant
    elif vehicle == "motorcycle" and sum(1 for d in detections if d.get("class_name") == "person") >= 3:
        violation_type = "triple_riding"

    return {"vehicle_type": vehicle, "violation_type": violation_type}


def generate_user_summary(
    detections: list[dict],
    ocr_result: dict,
    confidence: float,
    uncertainty: float,
    routing_decision: str,
    routing_rationale: str,
    primary_violation: dict | None,
    explanation: dict,
    scene_context: dict | None = None,
    signal_state: dict | None = None,
) -> dict:
    """Build a plain-language summary for the UI."""
    inferred = infer_from_detections(detections, scene_context, signal_state)

    grouped: dict[str, list] = {}
    for d in detections:
        name = d.get("class_name", "unknown")
        grouped.setdefault(name, []).append(d)

    found_items = []
    for cls, items in sorted(grouped.items()):
        label = FRIENDLY_NAMES.get(cls, cls.replace("_", " ").title())
        best_conf = max(i.get("confidence", 0) for i in items)
        found_items.append({"label": label, "count": len(items), "confidence": round(best_conf, 2)})

    # Add signal to found items
    sig = signal_state or {}
    if sig.get("state") and sig["state"] != "unknown":
        found_items.insert(0, {
            "label": f"Traffic signal: {sig['state'].upper()}",
            "count": 1,
            "confidence": round(sig.get("confidence", 0), 2),
        })

    plate = ocr_result.get("text") or None
    violation_type = None
    if primary_violation:
        violation_type = primary_violation.get("violation_type")
    elif inferred.get("violation_type"):
        violation_type = inferred["violation_type"]

    vlabel = FRIENDLY_VIOLATION_LABELS.get(violation_type or "", violation_type or "")

    if not detections and sig.get("state") == "unknown":
        headline = "Nothing detected in this image"
        verdict = "We couldn't identify vehicles or traffic signals. Try a clearer photo."
    elif primary_violation or violation_type:
        label = vlabel or (violation_type or "").replace("_", " ").title()
        headline = f"{label} detected"
        if violation_type == "red_light":
            verdict = (
                f"A vehicle appears to have crossed during a {sig.get('state', 'red').upper()} signal. "
                f"Signal confidence: {(sig.get('confidence', 0) * 100):.0f}%. "
                f"Overall case confidence: {(confidence * 100):.0f}%."
            )
        elif violation_type == "stop_line":
            verdict = "A vehicle was detected on the pedestrian crossing or beyond the stop line."
        else:
            verdict = f"Our AI flagged a {label.lower()} with {(confidence * 100):.0f}% confidence."
    else:
        headline = f"Found {len(found_items)} item{'s' if len(found_items) != 1 else ''} in the scene"
        labels = ", ".join(i["label"] for i in found_items[:4])
        verdict = f"We detected: {labels}. No traffic violation was confirmed."

    if plate:
        verdict += f" License plate: {plate}."

    return {
        "headline": headline,
        "verdict": verdict,
        "next_step": ROUTING_MESSAGES.get(routing_decision, routing_rationale),
        "found_items": found_items,
        "plate_number": plate,
        "vehicle_type": inferred.get("vehicle_type"),
        "inferred_violation_type": violation_type,
        "violation_label": vlabel,
        "routing_decision": routing_decision,
        "signal_state": sig.get("state"),
    }
