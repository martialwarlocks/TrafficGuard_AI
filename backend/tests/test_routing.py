from backend.app.services.routing import RoutingEngine
from backend.app.models import RoutingDecision


def test_auto_process_high_confidence():
    engine = RoutingEngine(auto_threshold=0.85, review_threshold=0.60)
    decision, rationale = engine.route(0.92, 0.08)
    assert decision == RoutingDecision.AUTO_PROCESS
    assert "High confidence" in rationale


def test_human_review_medium_confidence():
    engine = RoutingEngine(auto_threshold=0.85, review_threshold=0.60)
    decision, _ = engine.route(0.72, 0.28, ["Helmet partially occluded"])
    assert decision == RoutingDecision.HUMAN_REVIEW


def test_discard_low_confidence():
    engine = RoutingEngine(auto_threshold=0.85, review_threshold=0.60)
    decision, _ = engine.route(0.45, 0.55)
    assert decision == RoutingDecision.DISCARD


def test_confidence_formula():
    conf = RoutingEngine.calculate_final_confidence(0.8, 0.7, 0.9, 0.6)
    assert 0.7 < conf < 0.85
