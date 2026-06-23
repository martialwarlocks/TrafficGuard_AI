"""Detect traffic signal state from image using traffic-light ROIs."""

import cv2
import numpy as np
from dataclasses import dataclass


@dataclass
class TrafficSignalState:
    state: str  # red, green, yellow, unknown
    confidence: float
    red_pixel_ratio: float
    green_pixel_ratio: float
    region: tuple[int, int, int, int]  # x1,y1,x2,y2 of analyzed region

    def to_dict(self) -> dict:
        return {
            "state": self.state,
            "confidence": round(self.confidence, 3),
            "red_pixel_ratio": round(self.red_pixel_ratio, 4),
            "green_pixel_ratio": round(self.green_pixel_ratio, 4),
        }


class TrafficSignalDetector:
    """Detect red/green/yellow within YOLO traffic-light crops or compact signal blobs."""

    MIN_SIGNAL_CONF = 0.45
    MIN_RED_RATIO = 0.008
    MIN_GREEN_RATIO = 0.008

    def detect(
        self,
        image: np.ndarray,
        traffic_light_boxes: list[dict] | None = None,
        yolo_signal_detections: list[dict] | None = None,
    ) -> TrafficSignalState:
        """Analyze signal state. Prefer YOLO traffic-light boxes, then blob search."""
        h, w = image.shape[:2]

        # Direct YOLO red/green class detections from custom model
        if yolo_signal_detections:
            best_yolo = self._from_yolo_classes(yolo_signal_detections)
            if best_yolo.confidence >= self.MIN_SIGNAL_CONF:
                return best_yolo

        candidates: list[TrafficSignalState] = []

        if traffic_light_boxes:
            for box in traffic_light_boxes:
                bbox = box.get("bbox", [])
                if len(bbox) != 4:
                    continue
                x1, y1, x2, y2 = map(int, bbox)
                pad = 4
                x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
                x2, y2 = min(w, x2 + pad), min(h, y2 + pad)
                roi = image[y1:y2, x1:x2]
                if roi.size == 0:
                    continue
                state = self._analyze_roi(roi, (x1, y1, x2, y2), strict=True)
                if state.confidence > 0:
                    candidates.append(state)

        if not candidates:
            candidates.extend(self._find_signal_blobs(image))

        if not candidates:
            return TrafficSignalState("unknown", 0.0, 0.0, 0.0, (0, 0, 0, 0))

        best = max(candidates, key=lambda s: s.confidence)
        if best.confidence < self.MIN_SIGNAL_CONF:
            return TrafficSignalState(
                "unknown", 0.0, best.red_pixel_ratio, best.green_pixel_ratio, best.region
            )
        return best

    def _from_yolo_classes(self, detections: list[dict]) -> TrafficSignalState:
        mapping = {
            "traffic_light_red": "red",
            "traffic_light_green": "green",
            "traffic_light_yellow": "yellow",
            "red": "red",
            "green": "green",
            "yellow": "yellow",
        }
        best = TrafficSignalState("unknown", 0.0, 0.0, 0.0, (0, 0, 0, 0))
        for d in detections:
            name = d.get("class_name", "")
            state = mapping.get(name)
            if not state:
                continue
            conf = float(d.get("confidence", 0))
            if conf > best.confidence:
                bbox = d.get("bbox", [0, 0, 0, 0])
                region = tuple(map(int, bbox)) if len(bbox) == 4 else (0, 0, 0, 0)
                best = TrafficSignalState(state, conf, 0.0, 0.0, region)
        return best

    def _find_signal_blobs(self, image: np.ndarray) -> list[TrafficSignalState]:
        """Search upper frame for compact circular signal blobs (strict)."""
        h, w = image.shape[:2]
        regions = [
            (int(w * 0.02), 0, int(w * 0.38), int(h * 0.42)),
            (int(w * 0.32), 0, int(w * 0.68), int(h * 0.38)),
        ]
        found = []
        for x1, y1, x2, y2 in regions:
            roi = image[y1:y2, x1:x2]
            if roi.size == 0:
                continue
            state = self._analyze_roi(roi, (x1, y1, x2, y2), strict=True)
            if state.confidence > 0:
                found.append(state)
        return found

    def _analyze_roi(
        self, roi: np.ndarray, region: tuple, strict: bool = False
    ) -> TrafficSignalState:
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        total = roi.shape[0] * roi.shape[1]
        if total == 0:
            return TrafficSignalState("unknown", 0.0, 0.0, 0.0, region)

        # High saturation + value — actual lit signals, not red cars/signs
        sat_min = 120 if strict else 80
        val_min = 140 if strict else 80

        mask_red = (
            cv2.inRange(hsv, (0, sat_min, val_min), (10, 255, 255))
            | cv2.inRange(hsv, (170, sat_min, val_min), (180, 255, 255))
        )
        mask_green = cv2.inRange(hsv, (40, sat_min, val_min), (85, 255, 255))
        mask_yellow = cv2.inRange(hsv, (18, sat_min, val_min), (32, 255, 255))

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_OPEN, kernel)
        mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_OPEN, kernel)

        if strict:
            mask_red = self._keep_compact_blobs(mask_red, roi.shape)
            mask_green = self._keep_compact_blobs(mask_green, roi.shape)
            mask_yellow = self._keep_compact_blobs(mask_yellow, roi.shape)

        red_ratio = cv2.countNonZero(mask_red) / total
        green_ratio = cv2.countNonZero(mask_green) / total
        yellow_ratio = cv2.countNonZero(mask_yellow) / total

        min_red = self.MIN_RED_RATIO if strict else 0.002
        min_green = self.MIN_GREEN_RATIO if strict else 0.002
        dominance = 2.0 if strict else 1.5

        if red_ratio > min_red and red_ratio > green_ratio * dominance and red_ratio > yellow_ratio:
            conf = min(red_ratio * 40 + 0.35, 0.92)
            return TrafficSignalState("red", conf, red_ratio, green_ratio, region)
        if green_ratio > min_green and green_ratio > red_ratio * dominance:
            conf = min(green_ratio * 40 + 0.35, 0.92)
            return TrafficSignalState("green", conf, red_ratio, green_ratio, region)
        if yellow_ratio > min_red and yellow_ratio > red_ratio and yellow_ratio > green_ratio:
            conf = min(yellow_ratio * 35 + 0.3, 0.85)
            return TrafficSignalState("yellow", conf, red_ratio, green_ratio, region)

        return TrafficSignalState("unknown", 0.0, red_ratio, green_ratio, region)

    def _keep_compact_blobs(self, mask: np.ndarray, shape: tuple) -> np.ndarray:
        """Keep only small, roughly circular blobs (typical traffic-light lens)."""
        h, w = shape[:2]
        max_area = max(h * w * 0.08, 200)
        min_area = 30
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        out = np.zeros_like(mask)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area or area > max_area:
                continue
            perimeter = cv2.arcLength(cnt, True)
            if perimeter <= 0:
                continue
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity < 0.35:
                continue
            cv2.drawContours(out, [cnt], -1, 255, -1)
        return out
