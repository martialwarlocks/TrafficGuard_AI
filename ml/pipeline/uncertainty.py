import numpy as np
from dataclasses import dataclass


@dataclass
class UncertaintyResult:
    uncertainty_score: float
    prediction_variance: float
    class_entropy: float
    detection_stability: float
    mc_dropout_passes: int

    def to_dict(self) -> dict:
        return {
            "uncertainty_score": round(self.uncertainty_score, 4),
            "prediction_variance": round(self.prediction_variance, 4),
            "class_entropy": round(self.class_entropy, 4),
            "detection_stability": round(self.detection_stability, 4),
            "mc_dropout_passes": self.mc_dropout_passes,
        }


class UncertaintyEstimator:
    """Stage 5: MC Dropout uncertainty estimation."""

    def __init__(self, n_passes: int = 20):
        self.n_passes = n_passes

    def estimate(
        self,
        detections_per_pass: list[list],
        primary_detections: list,
    ) -> UncertaintyResult:
        if not detections_per_pass:
            return UncertaintyResult(1.0, 1.0, 1.0, 0.0, self.n_passes)

        confidences_all = []
        for pass_dets in detections_per_pass:
            confidences_all.extend([d.confidence for d in pass_dets])

        prediction_variance = float(np.var(confidences_all)) if confidences_all else 1.0

        class_counts: dict[str, int] = {}
        total = 0
        for d in primary_detections:
            class_counts[d.class_name] = class_counts.get(d.class_name, 0) + 1
            total += 1

        entropy = 0.0
        if total > 0:
            for count in class_counts.values():
                p = count / total
                if p > 0:
                    entropy -= p * np.log2(p)
            max_entropy = np.log2(max(len(class_counts), 1)) or 1
            class_entropy = entropy / max_entropy if max_entropy > 0 else 0
        else:
            class_entropy = 1.0

        counts = [len(d) for d in detections_per_pass]
        mean_count = np.mean(counts) if counts else 0
        detection_stability = 1.0 - min(float(np.var(counts)) / max(mean_count, 1), 1.0)

        uncertainty = (
            0.4 * min(prediction_variance * 4, 1.0)
            + 0.3 * class_entropy
            + 0.3 * (1.0 - detection_stability)
        )

        return UncertaintyResult(
            uncertainty_score=max(0.0, min(1.0, uncertainty)),
            prediction_variance=prediction_variance,
            class_entropy=class_entropy,
            detection_stability=detection_stability,
            mc_dropout_passes=self.n_passes,
        )
