from ml.violations.base import ViolationResult


def detect_stop_line_violation(
    detections: list,
    scene_context: dict | None = None,
    quality_score: float = 1.0,
    uncertainty: float = 0.0,
) -> ViolationResult | None:
    """Detect stop line / crosswalk encroachment."""
    ctx = scene_context or {}
    if not ctx.get("crosswalk_detected"):
        return None

    violators = ctx.get("vehicles_in_crosswalk", [])
    if not violators:
        return None

    conf = max(v.get("confidence", 0) for v in violators) * 0.82

    return ViolationResult(
        violation_type="stop_line",
        detected=True,
        confidence=round(conf, 4),
        uncertainty=uncertainty + 0.1,
        explanation={
            "confidence": round(conf, 4),
            "uncertainty": round(uncertainty + 0.1, 4),
            "reasons": [
                "Vehicle encroaching on pedestrian crossing or stop line",
                "Crosswalk detected in scene",
            ],
        },
        evidence={"vehicles": violators, "scene": ctx},
    )
