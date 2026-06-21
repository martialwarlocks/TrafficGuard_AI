from ml.violations.base import ViolationResult


def detect_parking_violation(detections: list, no_parking_zone: bool = False, dwell_time_seconds: float = 0, quality_score: float = 1.0, uncertainty: float = 0.0) -> ViolationResult | None:
    if not no_parking_zone:
        return None

    vehicles = [d for d in detections if d.get("class_name") in ("car", "motorcycle", "truck", "bus")]
    stationary = [v for v in vehicles if v.get("confidence", 0) > 0.4]

    if not stationary or dwell_time_seconds < 30:
        return None

    conf = max(v.get("confidence", 0) for v in stationary)
    return ViolationResult(
        violation_type="parking",
        detected=True,
        confidence=conf * 0.78,
        uncertainty=uncertainty + 0.1,
        explanation={
            "confidence": conf * 0.78,
            "uncertainty": uncertainty + 0.1,
            "reasons": [
                f"Vehicle stationary for {int(dwell_time_seconds)}s in no-parking zone",
                "Dwell time threshold exceeded",
            ],
        },
        evidence={"vehicles": stationary, "dwell_time": dwell_time_seconds},
    )
