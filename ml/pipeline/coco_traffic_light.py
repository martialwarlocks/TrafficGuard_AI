"""Detect traffic-light bounding boxes using COCO-pretrained YOLO."""

import numpy as np
from pathlib import Path

COCO_TRAFFIC_LIGHT_CLASS = 9


class COCOTrafficLightDetector:
    """Lightweight COCO YOLO pass — traffic light class only."""

    def __init__(self, model_path: str = "yolov8n.pt"):
        self.model_path = model_path
        self.model = None
        self._loaded = False

    def _load(self):
        if self._loaded:
            return
        from ultralytics import YOLO
        path = Path(self.model_path)
        self.model = YOLO(str(path) if path.exists() else "yolov8n.pt")
        self._loaded = True

    def detect(self, image: np.ndarray, conf: float = 0.35) -> list[dict]:
        self._load()
        results = self.model(image, conf=conf, classes=[COCO_TRAFFIC_LIGHT_CLASS], verbose=False)
        boxes = []
        for result in results:
            if result.boxes is None:
                continue
            for i in range(len(result.boxes)):
                xyxy = result.boxes.xyxy[i].cpu().numpy().tolist()
                score = float(result.boxes.conf[i].item())
                boxes.append({"bbox": xyxy, "confidence": score})
        return boxes
