from dataclasses import dataclass
from typing import Optional


@dataclass
class ViolationResult:
    violation_type: str
    detected: bool
    confidence: float
    uncertainty: float
    explanation: dict
    evidence: dict

    def to_dict(self) -> dict:
        return {
            "violation_type": self.violation_type,
            "detected": self.detected,
            "confidence": round(self.confidence, 4),
            "uncertainty": round(self.uncertainty, 4),
            "explanation": self.explanation,
            "evidence": self.evidence,
        }


def _find_nearby(detections: list, class_name: str, target_center: tuple, max_dist: float = 150) -> list:
    results = []
    for d in detections:
        if d.get("class_name") != class_name:
            continue
        cx, cy = d.get("center", [0, 0])
        tx, ty = target_center
        dist = ((cx - tx) ** 2 + (cy - ty) ** 2) ** 0.5
        if dist <= max_dist:
            results.append(d)
    return results
