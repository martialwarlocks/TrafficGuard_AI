import cv2
import numpy as np
import time
from pathlib import Path

from ml.pipeline.quality import ImageQualityAssessor
from ml.pipeline.enhancement import ImageEnhancer
from ml.pipeline.detection import YOLODetector
from ml.pipeline.ocr import PlateOCR
from ml.pipeline.uncertainty import UncertaintyEstimator
from ml.pipeline.explainability import ExplainabilityEngine
from ml.pipeline.traffic_signal import TrafficSignalDetector
from ml.pipeline.coco_traffic_light import COCOTrafficLightDetector
from ml.pipeline.scene_analysis import SceneAnalyzer
from ml.pipeline.summary import generate_user_summary
from ml.violations.catalog import VIOLATION_PRIORITY
from ml.violations.helmet_violation import detect_helmet_violation
from ml.violations.seatbelt_violation import detect_seatbelt_violation
from ml.violations.triple_riding import detect_triple_riding
from ml.violations.red_light import detect_red_light_violation
from ml.violations.wrong_side import detect_wrong_side
from ml.violations.stop_line import detect_stop_line_violation
from ml.violations.parking_violation import detect_parking_violation


class TrafficAnalyzer:
    """Complete AI pipeline orchestrator."""

    def __init__(self, model_path: str = "ml/models/yolov8s.pt", mc_passes: int = 20):
        self.quality_assessor = ImageQualityAssessor()
        self.enhancer = ImageEnhancer()
        self.detector = YOLODetector(model_path)
        self.ocr = PlateOCR()
        self.uncertainty_estimator = UncertaintyEstimator(n_passes=mc_passes)
        self.explainer = ExplainabilityEngine()
        self.signal_detector = TrafficSignalDetector()
        self.coco_tl_detector = COCOTrafficLightDetector()
        self.scene_analyzer = SceneAnalyzer()
        self.mc_passes = mc_passes

    def analyze(self, image_path: str, camera_id: int | None = None) -> dict:
        start = time.time()
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        quality = self.quality_assessor.assess(image)
        enhanced = self.enhancer.enhance(image)

        detections, mc_uncertainty = self.detector.detect_with_mc_dropout(
            enhanced, n_passes=self.mc_passes
        )
        det_dicts = [d.to_dict() for d in detections]

        # Traffic signal + scene context (critical for red light / stop line)
        tl_boxes = self.coco_tl_detector.detect(enhanced)
        signal_dets = [
            d for d in det_dicts
            if d.get("class_name") in (
                "traffic_light_red", "traffic_light_green", "traffic_light_yellow",
                "red", "green", "yellow",
            )
        ]
        signal = self.signal_detector.detect(
            enhanced, traffic_light_boxes=tl_boxes, yolo_signal_detections=signal_dets
        )
        scene = self.scene_analyzer.analyze(enhanced, det_dicts)
        scene_dict = {
            **scene.to_dict(),
            "vehicles_past_stop_line": scene.vehicles_past_stop_line,
            "vehicles_in_crosswalk": scene.vehicles_in_crosswalk,
            "image_height": enhanced.shape[0],
            "image_width": enhanced.shape[1],
        }
        signal_dict = signal.to_dict()

        plate_crop = self._extract_plate_crop(enhanced, detections)
        ocr_result = self.ocr.recognize(plate_crop if plate_crop is not None else enhanced)
        ocr_dict = ocr_result.to_dict()

        all_pass_dets = []
        for _ in range(self.mc_passes):
            pass_dets, _ = self.detector.detect_with_mc_dropout(enhanced, n_passes=1)
            all_pass_dets.append(pass_dets)

        uncertainty_result = self.uncertainty_estimator.estimate(all_pass_dets, detections)
        uncertainty = max(mc_uncertainty, uncertainty_result.uncertainty_score)

        model_conf = max((d.confidence for d in detections), default=0.0)
        stability = uncertainty_result.detection_stability

        # Run all violation detectors with scene context
        violations = self._detect_all_violations(
            det_dicts, quality.quality_score, uncertainty, scene_dict, signal_dict
        )

        # Pick highest-priority violation
        primary = self._select_primary_violation(violations)

        # Recalculate confidence when we have a confirmed violation
        if primary:
            final_confidence = (
                0.45 * primary["confidence"]
                + 0.2 * quality.quality_score
                + 0.2 * stability
                + 0.15 * (signal_dict.get("confidence", 0) if primary["violation_type"] == "red_light" else ocr_result.confidence)
            )
        else:
            final_confidence = (
                0.5 * model_conf
                + 0.2 * quality.quality_score
                + 0.2 * stability
                + 0.1 * ocr_result.confidence
            )

        explanation = self.explainer.explain(
            final_confidence, uncertainty, quality.to_dict(), det_dicts, ocr_dict
        )

        annotated = self._draw_annotations(enhanced.copy(), detections, signal_dict, scene)

        from backend.app.services.routing import RoutingEngine
        from backend.app.models import RoutingDecision
        from ml.pipeline.summary import infer_from_detections

        router = RoutingEngine()
        routing_decision, routing_rationale = router.route(
            final_confidence, uncertainty, explanation.reasons
        )

        inferred = infer_from_detections(det_dicts, scene_dict, signal_dict)
        if not violations and inferred.get("violation_type"):
            routing_decision = RoutingDecision.HUMAN_REVIEW
            routing_rationale = (
                f"Possible {inferred['violation_type'].replace('_', ' ')} violation detected "
                f"but not confirmed with high enough confidence. Officer review required."
            )

        processing_ms = (time.time() - start) * 1000

        user_summary = generate_user_summary(
            det_dicts, ocr_dict, final_confidence, uncertainty,
            routing_decision.value, routing_rationale,
            primary, explanation.to_dict(),
            scene_dict, signal_dict,
        )

        return {
            "camera_id": camera_id,
            "quality_metrics": quality.to_dict(),
            "detections": det_dicts,
            "ocr_result": ocr_dict,
            "violations": violations,
            "primary_violation": primary,
            "confidence": round(final_confidence, 4),
            "uncertainty": round(uncertainty, 4),
            "model_confidence": round(model_conf, 4),
            "stability_score": round(stability, 4),
            "explanation": explanation.to_dict(),
            "routing_decision": routing_decision.value,
            "routing_rationale": routing_rationale,
            "uncertainty_details": uncertainty_result.to_dict(),
            "traffic_signal": signal_dict,
            "scene_context": scene_dict,
            "annotated_image": annotated,
            "enhanced_image": enhanced,
            "processing_time_ms": round(processing_ms, 2),
            "user_summary": user_summary,
        }

    def _detect_all_violations(
        self, det_dicts, quality_score, uncertainty, scene_dict, signal_dict
    ) -> list[dict]:
        found = []

        rl = detect_red_light_violation(
            det_dicts,
            traffic_signal_state=signal_dict.get("state", "unknown"),
            signal_confidence=signal_dict.get("confidence", 0),
            scene_context=scene_dict,
            quality_score=quality_score,
            uncertainty=uncertainty,
        )
        if rl and rl.detected:
            found.append(rl.to_dict())

        sl = detect_stop_line_violation(
            det_dicts, scene_context=scene_dict, quality_score=quality_score, uncertainty=uncertainty
        )
        if sl and sl.detected:
            found.append(sl.to_dict())

        for fn in (detect_helmet_violation, detect_seatbelt_violation, detect_triple_riding):
            result = fn(det_dicts, quality_score, uncertainty)
            if result and result.detected:
                found.append(result.to_dict())

        det_classes = {d.get("class_name") for d in det_dicts}
        found_types = {v["violation_type"] for v in found}

        # Explicit detections beat heuristic stop_line / parking
        if "no_helmet" in det_classes:
            found = [v for v in found if v["violation_type"] not in ("stop_line", "seatbelt", "parking")]
        if "no_seatbelt" in det_classes:
            found = [v for v in found if v["violation_type"] not in ("stop_line", "parking")]

        if "red_light" in found_types:
            found = [v for v in found if v["violation_type"] not in ("seatbelt", "helmet", "parking")]
        if "stop_line" in found_types and "red_light" not in found_types:
            found = [v for v in found if v["violation_type"] != "parking"]

        return found

    def _select_primary_violation(self, violations: list[dict]) -> dict | None:
        if not violations:
            return None
        for vtype in VIOLATION_PRIORITY:
            for v in violations:
                if v.get("violation_type") == vtype:
                    return v
        return violations[0]

    def _extract_plate_crop(self, image: np.ndarray, detections: list):
        plates = [d for d in detections if d.class_name == "license_plate"]
        if not plates:
            return None
        best = max(plates, key=lambda d: d.confidence)
        x1, y1, x2, y2 = map(int, best.bbox)
        h, w = image.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        return image[y1:y2, x1:x2]

    def _draw_annotations(self, image, detections, signal_dict, scene) -> np.ndarray:
        colors = {
            "helmet": (0, 255, 0), "no_helmet": (0, 0, 255),
            "motorcycle": (255, 165, 0), "car": (255, 255, 0),
            "license_plate": (0, 255, 255), "person": (255, 0, 255),
            "truck": (0, 165, 255), "bus": (255, 0, 128),
        }
        for det in detections:
            x1, y1, x2, y2 = map(int, det.bbox)
            color = colors.get(det.class_name, (200, 200, 200))
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            label = f"{det.class_name} {det.confidence:.2f}"
            cv2.putText(image, label, (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Highlight crosswalk violators in red
        for v in scene.vehicles_in_crosswalk:
            bbox = v.get("bbox", [])
            if len(bbox) == 4:
                x1, y1, x2, y2 = map(int, bbox)
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 3)
                cv2.putText(image, "VIOLATION", (x1, y2 + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Signal state overlay
        sig = signal_dict.get("state", "unknown")
        if sig != "unknown":
            color = (0, 0, 255) if sig == "red" else (0, 255, 0) if sig == "green" else (0, 255, 255)
            cv2.putText(image, f"SIGNAL: {sig.upper()}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        return image
