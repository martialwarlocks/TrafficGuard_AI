import cv2
import numpy as np
from dataclasses import dataclass


@dataclass
class QualityMetrics:
    blur_score: float
    brightness: float
    noise_level: float
    contrast: float
    quality_score: float

    def to_dict(self) -> dict:
        return {
            "blur_score": round(self.blur_score, 4),
            "brightness": round(self.brightness, 4),
            "noise_level": round(self.noise_level, 4),
            "contrast": round(self.contrast, 4),
            "quality_score": round(self.quality_score, 4),
        }


class ImageQualityAssessor:
    """Stage 1: Image Quality Assessment."""

    def assess(self, image: np.ndarray) -> QualityMetrics:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        blur = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_score = min(blur / 500.0, 1.0)

        brightness = np.mean(gray) / 255.0

        noise = cv2.fastNlMeansDenoising(gray)
        noise_level = 1.0 - min(np.mean(np.abs(gray.astype(float) - noise.astype(float))) / 50.0, 1.0)

        contrast = gray.std() / 128.0
        contrast = min(contrast, 1.0)

        quality_score = (
            0.35 * blur_score
            + 0.25 * (1.0 - abs(brightness - 0.5) * 2)
            + 0.20 * noise_level
            + 0.20 * contrast
        )

        return QualityMetrics(
            blur_score=blur_score,
            brightness=brightness,
            noise_level=noise_level,
            contrast=contrast,
            quality_score=max(0.0, min(1.0, quality_score)),
        )
