from ml.violations.base import ViolationResult


def detect_triple_riding(detections: list, quality_score: float, uncertainty: float) -> ViolationResult | None:
    motorcycles = [d for d in detections if d.get("class_name") == "motorcycle"]
    if not motorcycles:
        return None

    for bike in motorcycles:
        center = tuple(bike.get("center", [0, 0]))
        bx1, by1, bx2, by2 = bike.get("bbox", [0, 0, 0, 0])
        riders = []
        for d in detections:
            if d.get("class_name") != "person":
                continue
            cx, cy = d.get("center", [0, 0])
            if bx1 <= cx <= bx2 and by1 <= cy <= by2:
                riders.append(d)

        if len(riders) >= 3:
            conf = min(r.get("confidence", 0.5) for r in riders)
            return ViolationResult(
                violation_type="triple_riding",
                detected=True,
                confidence=conf,
                uncertainty=uncertainty,
                explanation={
                    "confidence": conf,
                    "uncertainty": uncertainty,
                    "reasons": [f"{len(riders)} riders detected on single motorcycle"],
                },
                evidence={"motorcycle": bike, "riders": riders, "rider_count": len(riders)},
            )
    return None
