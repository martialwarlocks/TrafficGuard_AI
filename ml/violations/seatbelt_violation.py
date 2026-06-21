from ml.violations.base import ViolationResult, _find_nearby


def detect_seatbelt_violation(detections: list, quality_score: float, uncertainty: float) -> ViolationResult | None:
    cars = [d for d in detections if d.get("class_name") in ("car", "truck", "bus")]
    no_seatbelts = [d for d in detections if d.get("class_name") == "no_seatbelt"]

    if not cars and not no_seatbelts:
        persons = [d for d in detections if d.get("class_name") == "person"]
        if not persons:
            return None

    violations = []
    for vehicle in cars:
        center = tuple(vehicle.get("center", [0, 0]))
        nearby_no_sb = _find_nearby(detections, "no_seatbelt", center, max_dist=200)
        nearby_sb = _find_nearby(detections, "seatbelt", center, max_dist=200)

        if nearby_no_sb and not nearby_sb:
            conf = max(d.get("confidence", 0) for d in nearby_no_sb)
            violations.append((vehicle, conf, nearby_no_sb))

    if not violations and no_seatbelts:
        conf = max(d.get("confidence", 0) for d in no_seatbelts)
        violations.append((no_seatbelts[0], conf, no_seatbelts))

    if not violations:
        return None

    best = max(violations, key=lambda x: x[1])
    _, conf, evidence = best

    reasons = ["Seatbelt not detected on occupant"]
    if quality_score < 0.5:
        reasons.append("Low image quality affecting visibility")

    return ViolationResult(
        violation_type="seatbelt",
        detected=True,
        confidence=conf,
        uncertainty=uncertainty,
        explanation={"confidence": conf, "uncertainty": uncertainty, "reasons": reasons},
        evidence={"detections": evidence},
    )
