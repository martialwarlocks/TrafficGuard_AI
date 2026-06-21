from backend.app.config import get_settings
from backend.app.models import RoutingDecision

settings = get_settings()


class RoutingEngine:
    """Uncertainty-aware violation routing engine."""

    def __init__(
        self,
        auto_threshold: float | None = None,
        review_threshold: float | None = None,
    ):
        self.auto_threshold = auto_threshold or settings.auto_process_threshold
        self.review_threshold = review_threshold or settings.human_review_threshold

    def route(self, confidence: float, uncertainty: float, reasons: list[str] | None = None) -> tuple[RoutingDecision, str]:
        if confidence >= self.auto_threshold:
            decision = RoutingDecision.AUTO_PROCESS
            rationale = (
                f"High confidence ({confidence:.2%}) exceeds auto-process threshold "
                f"({self.auto_threshold:.2%}). Uncertainty is low at {uncertainty:.2%}."
            )
        elif confidence >= self.review_threshold:
            decision = RoutingDecision.HUMAN_REVIEW
            reason_text = ", ".join(reasons[:3]) if reasons else "borderline confidence"
            rationale = (
                f"Medium confidence ({confidence:.2%}) requires human review. "
                f"Uncertainty factors: {reason_text}."
            )
        else:
            decision = RoutingDecision.DISCARD
            rationale = (
                f"Low confidence ({confidence:.2%}) below discard threshold "
                f"({self.review_threshold:.2%}). Insufficient evidence for enforcement."
            )
        return decision, rationale

    @staticmethod
    def calculate_final_confidence(
        model_confidence: float,
        quality_score: float,
        stability_score: float,
        ocr_confidence: float,
    ) -> float:
        return (
            0.5 * model_confidence
            + 0.2 * quality_score
            + 0.2 * stability_score
            + 0.1 * ocr_confidence
        )


routing_engine = RoutingEngine()
