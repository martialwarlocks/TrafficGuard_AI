from ml.violations.base import ViolationResult


def detect_wrong_side(detections: list, lane_direction: str = "right", quality_score: float = 1.0, uncertainty: float = 0.0) -> ViolationResult | None:
    vehicles = [d for d in detections if d.get("class_name") in ("car", "motorcycle", "truck", "bus")]
    if not vehicles:
        return None

    for v in vehicles:
        bbox = v.get("bbox", [0, 0, 0, 0])
        cx = (bbox[0] + bbox[2]) / 2
        if lane_direction == "right" and cx < 0:
            conf = v.get("confidence", 0.5)
            return ViolationResult(
                violation_type="wrong_side",
                detected=True,
                confidence=conf * 0.8,
                uncertainty=uncertainty + 0.15,
                explanation={
                    "confidence": conf * 0.8,
                    "uncertainty": uncertainty + 0.15,
                    "reasons": ["Vehicle detected on wrong side of road", "Lane direction inference required"],
                },
                evidence={"vehicle": v, "lane_direction": lane_direction},
            )
    return None
