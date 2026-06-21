"""Detect traffic signal state from image using color analysis."""

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
    """Detect red/green traffic lights via HSV color analysis in signal regions."""

    def detect(self, image: np.ndarray) -> TrafficSignalState:
        h, w = image.shape[:2]

        # Traffic signals typically appear in upper-left or upper-center of CCTV frames
        regions = [
            (0, 0, int(w * 0.35), int(h * 0.45)),           # upper-left
            (int(w * 0.3), 0, int(w * 0.7), int(h * 0.40)),  # upper-center
            (0, 0, int(w * 0.5), int(h * 0.35)),             # broad upper-left
        ]

        best = TrafficSignalState("unknown", 0.0, 0.0, 0.0, (0, 0, 0, 0))

        for x1, y1, x2, y2 in regions:
            roi = image[y1:y2, x1:x2]
            if roi.size == 0:
                continue
            state = self._analyze_roi(roi, (x1, y1, x2, y2))
            if state.confidence > best.confidence:
                best = state

        return best

    def _analyze_roi(self, roi: np.ndarray, region: tuple) -> TrafficSignalState:
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        total = roi.shape[0] * roi.shape[1]

        # Red wraps around in HSV
        mask_red = cv2.inRange(hsv, (0, 80, 80), (12, 255, 255)) | cv2.inRange(
            hsv, (165, 80, 80), (180, 255, 255)
        )
        mask_green = cv2.inRange(hsv, (35, 40, 40), (90, 255, 255))
        mask_yellow = cv2.inRange(hsv, (15, 80, 80), (35, 255, 255))

        # Focus on bright saturated blobs (actual lights, not reflections)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_OPEN, kernel)
        mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_OPEN, kernel)

        red_ratio = cv2.countNonZero(mask_red) / max(total, 1)
        green_ratio = cv2.countNonZero(mask_green) / max(total, 1)
        yellow_ratio = cv2.countNonZero(mask_yellow) / max(total, 1)

        # Require minimum signal strength
        if red_ratio > 0.002 and red_ratio > green_ratio * 1.5:
            conf = min(red_ratio * 80, 0.95)
            return TrafficSignalState("red", conf, red_ratio, green_ratio, region)
        if green_ratio > 0.002 and green_ratio > red_ratio * 1.5:
            conf = min(green_ratio * 80, 0.95)
            return TrafficSignalState("green", conf, red_ratio, green_ratio, region)
        if yellow_ratio > 0.002:
            conf = min(yellow_ratio * 60, 0.85)
            return TrafficSignalState("yellow", conf, red_ratio, green_ratio, region)

        return TrafficSignalState("unknown", 0.0, red_ratio, green_ratio, region)
