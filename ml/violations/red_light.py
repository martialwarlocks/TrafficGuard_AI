from ml.violations.base import ViolationResult

SIGNAL_CLASSES = {"traffic_light_red", "red", "traffic_light_yellow", "yellow"}
VEHICLE_CLASSES = {"car", "motorcycle", "truck", "bus", "bicycle"}


def detect_red_light_violation(
    detections: list,
    traffic_signal_state: str = "unknown",
    signal_confidence: float = 0.0,
    scene_context: dict | None = None,
    quality_score: float = 1.0,
    uncertainty: float = 0.0,
) -> ViolationResult | None:
    """Detect red-light violation — requires red signal AND vehicle in intersection."""
    ctx = scene_context or {}

    # YOLO-detected red/yellow traffic light class
    yolo_red = [
        d for d in detections
        if d.get("class_name") in SIGNAL_CLASSES
        and d.get("confidence", 0) > 0.45
    ]
    signal_is_red = traffic_signal_state in ("red", "yellow") and signal_confidence >= 0.45
    if yolo_red:
        signal_is_red = True
        signal_confidence = max(signal_confidence, max(d["confidence"] for d in yolo_red))

    if not signal_is_red:
        return None

    vehicles_crosswalk = ctx.get("vehicles_in_crosswalk", [])
    vehicles_past = ctx.get("vehicles_past_stop_line", [])
    crosswalk_detected = ctx.get("crosswalk_detected", False)

    # Require vehicle actually in intersection — never flag from signal alone
    if vehicles_crosswalk:
        violators = vehicles_crosswalk
    elif crosswalk_detected and vehicles_past:
        violators = vehicles_past
    else:
        # No crosswalk evidence: only flag if vehicle center is in lower intersection zone
        violators = _vehicles_in_intersection_zone(detections, ctx)
        if not violators:
            return None

    best = max(violators, key=lambda v: v.get("confidence", 0))
    base_conf = best.get("confidence", 0.5)
    conf = base_conf * 0.55 + signal_confidence * 0.45
    if vehicles_crosswalk:
        conf = min(conf + 0.12, 0.94)
    if yolo_red:
        conf = min(conf + 0.08, 0.96)

    reasons = [
        f"Traffic signal: {traffic_signal_state.upper()} ({signal_confidence:.0%} confidence)",
    ]
    if vehicles_crosswalk:
        reasons.append("Vehicle detected on pedestrian crossing during red signal")
    elif crosswalk_detected:
        reasons.append("Vehicle past stop line while signal is red")
    else:
        reasons.append("Vehicle in intersection zone during red signal")
    if quality_score < 0.5:
        reasons.append("Low visibility — officer review recommended")

    return ViolationResult(
        violation_type="red_light",
        detected=True,
        confidence=round(conf, 4),
        uncertainty=uncertainty + (0.08 if signal_confidence < 0.55 else 0.0),
        explanation={
            "confidence": round(conf, 4),
            "uncertainty": round(uncertainty + (0.08 if signal_confidence < 0.55 else 0.0), 4),
            "reasons": reasons,
        },
        evidence={
            "vehicles": violators,
            "signal_state": traffic_signal_state,
            "signal_confidence": signal_confidence,
            "scene": ctx,
        },
    )


def _vehicles_in_intersection_zone(detections: list, ctx: dict) -> list[dict]:
    """Strict fallback: vehicle front must be in lower 32% of frame."""
    img_h = ctx.get("image_height") or 1080
    threshold_y = img_h * 0.68
    center_min = img_h * 0.55

    zone_vehicles = []
    for v in detections:
        if v.get("class_name") not in VEHICLE_CLASSES:
            continue
        if v.get("confidence", 0) < 0.45:
            continue
        bbox = v.get("bbox", [0, 0, 0, 0])
        if len(bbox) != 4:
            continue
        front_y = bbox[3]
        cy = (bbox[1] + bbox[3]) / 2
        if front_y >= threshold_y and cy >= center_min:
            zone_vehicles.append(v)
    return zone_vehicles
