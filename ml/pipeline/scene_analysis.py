"""Analyze intersection scene context for signal and crosswalk violations."""

import cv2
import numpy as np
from dataclasses import dataclass


@dataclass
class SceneContext:
    crosswalk_detected: bool
    crosswalk_y_start: float | None  # normalized 0-1 from top
    crosswalk_y_end: float | None
    vehicles_past_stop_line: list[dict]
    vehicles_in_crosswalk: list[dict]
    is_intersection: bool

    def to_dict(self) -> dict:
        return {
            "crosswalk_detected": self.crosswalk_detected,
            "crosswalk_y_start": self.crosswalk_y_start,
            "crosswalk_y_end": self.crosswalk_y_end,
            "vehicles_past_stop_line_count": len(self.vehicles_past_stop_line),
            "vehicles_in_crosswalk_count": len(self.vehicles_in_crosswalk),
            "is_intersection": self.is_intersection,
        }


VEHICLE_CLASSES = {"car", "motorcycle", "truck", "bus", "bicycle"}


class SceneAnalyzer:
    """Detect crosswalks and vehicle position relative to stop lines."""

    def analyze(self, image: np.ndarray, detections: list[dict]) -> SceneContext:
        h, w = image.shape[:2]
        crosswalk_y_start, crosswalk_y_end, crosswalk_detected = self._detect_crosswalk(image)

        vehicles = [d for d in detections if d.get("class_name") in VEHICLE_CLASSES]
        vehicles_in_crosswalk = []
        vehicles_past_stop_line = []

        stop_line_y = crosswalk_y_start * h if crosswalk_y_start else h * 0.55

        for v in vehicles:
            bbox = v.get("bbox", [0, 0, 0, 0])
            cx = (bbox[0] + bbox[2]) / 2
            cy = (bbox[1] + bbox[3]) / 2
            front_y = bbox[3]  # bottom of bbox = front of vehicle facing camera

            if crosswalk_detected and crosswalk_y_start and crosswalk_y_end:
                cw_start = crosswalk_y_start * h
                cw_end = crosswalk_y_end * h
                # Vehicle overlaps crosswalk band
                if front_y >= cw_start and bbox[1] <= cw_end:
                    vehicles_in_crosswalk.append(v)
                # Vehicle front past start of crosswalk (entered intersection)
                if front_y >= cw_start:
                    vehicles_past_stop_line.append(v)
            else:
                # Heuristic: lower half of frame = intersection area for front-facing CCTV
                if front_y >= stop_line_y:
                    vehicles_past_stop_line.append(v)
                if cy >= h * 0.45 and cy <= h * 0.75:
                    vehicles_in_crosswalk.append(v)

        is_intersection = crosswalk_detected or len(vehicles) >= 2

        return SceneContext(
            crosswalk_detected=crosswalk_detected,
            crosswalk_y_start=crosswalk_y_start,
            crosswalk_y_end=crosswalk_y_end,
            vehicles_past_stop_line=vehicles_past_stop_line,
            vehicles_in_crosswalk=vehicles_in_crosswalk,
            is_intersection=is_intersection,
        )

    def _detect_crosswalk(self, image: np.ndarray) -> tuple[float | None, float | None, bool]:
        """Detect zebra crossing via horizontal white stripe patterns."""
        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Focus on road area (middle-lower portion)
        roi = gray[int(h * 0.35): int(h * 0.85), :]
        if roi.size == 0:
            return None, None, False

        _, binary = cv2.threshold(roi, 180, 255, cv2.THRESH_BINARY)

        # Horizontal projection — zebra crossings have alternating bands
        row_sums = np.sum(binary, axis=1) / w
        threshold = np.mean(row_sums) + np.std(row_sums) * 0.5
        bright_rows = np.where(row_sums > threshold)[0]

        if len(bright_rows) < 3:
            return None, None, False

        # Check for stripe pattern (alternating bright/dim)
        gaps = np.diff(bright_rows)
        stripe_pattern = np.any((gaps > 2) & (gaps < 25))

        if not stripe_pattern and len(bright_rows) < 5:
            return None, None, False

        y_start = (int(h * 0.35) + bright_rows[0]) / h
        y_end = (int(h * 0.35) + bright_rows[-1]) / h
        return y_start, y_end, True
