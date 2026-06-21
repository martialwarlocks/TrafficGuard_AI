from ml.violations.base import ViolationResult, _find_nearby


def detect_helmet_violation(detections: list, quality_score: float, uncertainty: float) -> ViolationResult | None:
    motorcycles = [d for d in detections if d.get("class_name") == "motorcycle"]
    persons = [d for d in detections if d.get("class_name") == "person"]
    no_helmets = [d for d in detections if d.get("class_name") == "no_helmet"]
    helmets = [d for d in detections if d.get("class_name") == "helmet"]

    targets = motorcycles or persons
    if not targets:
        return None

    violations_found = []
    for target in targets:
        center = tuple(target.get("center", [0, 0]))
        nearby_no_helmet = _find_nearby(detections, "no_helmet", center)
        nearby_helmet = _find_nearby(detections, "helmet", center)

        if nearby_no_helmet and not nearby_helmet:
            conf = max(d.get("confidence", 0) for d in nearby_no_helmet)
            violations_found.append((target, conf, nearby_no_helmet))
        elif nearby_no_helmet and nearby_helmet:
            conf = max(d.get("confidence", 0) for d in nearby_no_helmet) * 0.7
            violations_found.append((target, conf, nearby_no_helmet))

    if not violations_found:
        return None

    best = max(violations_found, key=lambda x: x[1])
    target, conf, evidence_dets = best

    reasons = []
    if quality_score < 0.5:
        reasons.append("Low image quality")
    if uncertainty > 0.3:
        reasons.append("Detection instability")
    if any(d.get("confidence", 1) < 0.6 for d in evidence_dets):
        reasons.append("Helmet partially occluded")

    return ViolationResult(
        violation_type="helmet",
        detected=True,
        confidence=conf,
        uncertainty=uncertainty,
        explanation={"confidence": conf, "uncertainty": uncertainty, "reasons": reasons or ["No helmet detected on rider"]},
        evidence={"target": target, "detections": evidence_dets},
    )
