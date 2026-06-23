import numpy as np
from dataclasses import dataclass, field
from pathlib import Path


CLASS_NAMES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    4: "bus",
    5: "truck",
    6: "helmet",
    7: "no_helmet",
    8: "seatbelt",
    9: "no_seatbelt",
    10: "license_plate",
    11: "traffic_light_red",
    12: "traffic_light_green",
    13: "traffic_light_yellow",
}


@dataclass
class Detection:
    class_id: int
    class_name: str
    confidence: float
    bbox: list[float]
    center: tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))

    def to_dict(self) -> dict:
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": round(self.confidence, 4),
            "bbox": [round(x, 2) for x in self.bbox],
            "center": [round(self.center[0], 2), round(self.center[1], 2)],
        }


class YOLODetector:
    """Stage 3: YOLOv8s Detection."""

    def __init__(self, model_path: str = "ml/models/yolov8s.pt"):
        self.model_path = model_path
        self.model = None
        self._loaded = False

    def _load_model(self):
        if self._loaded:
            return
        try:
            from ultralytics import YOLO
            path = Path(self.model_path)
            if path.exists():
                self.model = YOLO(str(path))
            else:
                self.model = YOLO("yolov8s.pt")
            self._loaded = True
        except Exception as e:
            raise RuntimeError(f"Failed to load YOLO model: {e}")

    def detect(self, image: np.ndarray, conf_threshold: float = 0.25) -> list[Detection]:
        self._load_model()
        results = self.model(image, conf=conf_threshold, verbose=False)
        detections = []

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for i in range(len(boxes)):
                cls_id = int(boxes.cls[i].item())
                conf = float(boxes.conf[i].item())
                xyxy = boxes.xyxy[i].cpu().numpy().tolist()
                cx = (xyxy[0] + xyxy[2]) / 2
                cy = (xyxy[1] + xyxy[3]) / 2
                class_name = CLASS_NAMES.get(cls_id, result.names.get(cls_id, f"class_{cls_id}"))
                detections.append(Detection(
                    class_id=cls_id,
                    class_name=class_name,
                    confidence=conf,
                    bbox=xyxy,
                    center=(cx, cy),
                ))

        return detections

    def detect_with_mc_dropout(
        self, image: np.ndarray, n_passes: int = 20, conf_threshold: float = 0.25
    ) -> tuple[list[Detection], float]:
        """MC Dropout uncertainty estimation via detection stability."""
        self._load_model()
        all_pass_detections: list[list[Detection]] = []

        for _ in range(n_passes):
            results = self.model(image, conf=conf_threshold, verbose=False)
            pass_dets = []
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue
                for i in range(len(boxes)):
                    cls_id = int(boxes.cls[i].item())
                    conf = float(boxes.conf[i].item())
                    xyxy = boxes.xyxy[i].cpu().numpy().tolist()
                    class_name = CLASS_NAMES.get(cls_id, result.names.get(cls_id, f"class_{cls_id}"))
                    pass_dets.append(Detection(cls_id, class_name, conf, xyxy))
            all_pass_detections.append(pass_dets)

        if not all_pass_detections or not any(all_pass_detections):
            return [], 1.0

        primary = all_pass_detections[0]
        if len(primary) == 0:
            return [], 1.0

        confidences = [d.confidence for d in primary]
        avg_conf = np.mean(confidences)

        detection_counts = [len(d) for d in all_pass_detections]
        count_variance = np.var(detection_counts) / max(np.mean(detection_counts), 1)
        stability = 1.0 - min(count_variance, 1.0)

        class_sets = [set(d.class_name for d in pd) for pd in all_pass_detections]
        if class_sets:
            union = set.union(*class_sets) if class_sets else set()
            intersection = set.intersection(*class_sets) if class_sets else set()
            jaccard = len(intersection) / max(len(union), 1)
            stability = 0.5 * stability + 0.5 * jaccard

        uncertainty = 1.0 - stability
        return primary, uncertainty
