from dataclasses import dataclass


@dataclass
class ExplanationResult:
    confidence: float
    uncertainty: float
    reasons: list[str]

    def to_dict(self) -> dict:
        return {
            "confidence": round(self.confidence, 4),
            "uncertainty": round(self.uncertainty, 4),
            "reasons": self.reasons,
        }


class ExplainabilityEngine:
    """Generate natural-language explanations for enforcement decisions."""

    def explain(
        self,
        confidence: float,
        uncertainty: float,
        quality_metrics: dict,
        detections: list,
        ocr_result: dict | None = None,
    ) -> ExplanationResult:
        reasons = []

        if quality_metrics.get("blur_score", 1.0) < 0.4:
            reasons.append("Motion blur detected")
        if quality_metrics.get("brightness", 0.5) < 0.3:
            reasons.append("Poor lighting conditions")
        elif quality_metrics.get("brightness", 0.5) > 0.85:
            reasons.append("Overexposed image")
        if quality_metrics.get("quality_score", 1.0) < 0.5:
            reasons.append("Low image quality")
        if quality_metrics.get("noise_level", 1.0) < 0.4:
            reasons.append("High noise level in capture")
        if quality_metrics.get("contrast", 1.0) < 0.3:
            reasons.append("Low contrast affecting detection")

        helmet_dets = [d for d in detections if "helmet" in d.get("class_name", "")]
        if helmet_dets:
            min_conf = min(d.get("confidence", 1.0) for d in helmet_dets)
            if 0.3 < min_conf < 0.7:
                reasons.append("Helmet partially occluded")

        if ocr_result:
            if ocr_result.get("confidence", 1.0) < 0.6:
                reasons.append("Low OCR confidence on plate")
            alts = ocr_result.get("alternatives", [])
            if len(alts) > 0 and alts[0].get("text") != ocr_result.get("text"):
                reasons.append("OCR disagreement between candidates")

        if uncertainty > 0.5:
            reasons.append("Detection instability across MC Dropout passes")

        no_helmet = any(d.get("class_name") == "no_helmet" for d in detections)
        helmet = any(d.get("class_name") == "helmet" for d in detections)
        if no_helmet and helmet:
            reasons.append("Conflicting helmet/no-helmet detections")

        if not reasons:
            if confidence >= 0.85:
                reasons.append("High-quality capture with stable detections")
            elif confidence >= 0.60:
                reasons.append("Borderline detection requiring review")
            else:
                reasons.append("Insufficient evidence for reliable detection")

        return ExplanationResult(
            confidence=confidence,
            uncertainty=uncertainty,
            reasons=reasons,
        )
