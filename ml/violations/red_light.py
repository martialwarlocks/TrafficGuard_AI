from ml.violations.base import ViolationResult


def detect_red_light_violation(
    detections: list,
    traffic_signal_state: str = "unknown",
    signal_confidence: float = 0.0,
    scene_context: dict | None = None,
    quality_score: float = 1.0,
    uncertainty: float = 0.0,
) -> ViolationResult | None:
    """Detect red light / signal jump using traffic signal state + vehicle position."""
    if traffic_signal_state not in ("red", "yellow"):
        return None

    ctx = scene_context or {}
    vehicles_past = ctx.get("vehicles_past_stop_line", [])
    vehicles_crosswalk = ctx.get("vehicles_in_crosswalk", [])

    # Prefer vehicles in crosswalk; fall back to any vehicle past stop line
    violators = vehicles_crosswalk or vehicles_past
    if not violators:
        vehicles = [d for d in detections if d.get("class_name") in ("car", "motorcycle", "truck", "bus")]
        violators = [v for v in vehicles if v.get("confidence", 0) > 0.35]

    if not violators:
        return None

    best = max(violators, key=lambda v: v.get("confidence", 0))
    base_conf = best.get("confidence", 0.5)

    # Boost confidence when signal is clearly red and vehicle is on crosswalk
    conf = base_conf * 0.7 + signal_confidence * 0.3
    if vehicles_crosswalk:
        conf = min(conf + 0.15, 0.92)
    if traffic_signal_state == "red" and signal_confidence > 0.3:
        conf = min(conf + 0.1, 0.95)

    reasons = [
        f"Traffic signal detected as {traffic_signal_state.upper()} ({signal_confidence:.0%} confidence)",
    ]
    if vehicles_crosswalk:
        reasons.append("Vehicle detected on pedestrian crossing / past stop line")
    else:
        reasons.append("Vehicle detected in intersection during red signal")
    if quality_score < 0.5:
        reasons.append("Low visibility due to image quality — officer review recommended")

    return ViolationResult(
        violation_type="red_light",
        detected=True,
        confidence=round(conf, 4),
        uncertainty=uncertainty + (0.05 if signal_confidence < 0.5 else 0.0),
        explanation={
            "confidence": round(conf, 4),
            "uncertainty": round(uncertainty + (0.05 if signal_confidence < 0.5 else 0.0), 4),
            "reasons": reasons,
        },
        evidence={
            "vehicles": violators,
            "signal_state": traffic_signal_state,
            "signal_confidence": signal_confidence,
            "scene": ctx,
        },
    )
