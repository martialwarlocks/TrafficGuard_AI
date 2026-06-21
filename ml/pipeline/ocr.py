import re
from dataclasses import dataclass


@dataclass
class OCRResult:
    text: str
    confidence: float
    alternatives: list[dict]

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "confidence": round(self.confidence, 4),
            "alternatives": self.alternatives,
        }


class PlateOCR:
    """Stage 4: PaddleOCR for license plate recognition."""

    def __init__(self):
        self.ocr = None
        self._loaded = False

    def _load_model(self):
        if self._loaded:
            return
        try:
            from paddleocr import PaddleOCR
            self.ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False, use_gpu=False)
            self._loaded = True
        except Exception:
            self.ocr = None
            self._loaded = True

    def recognize(self, image) -> OCRResult:
        self._load_model()
        if self.ocr is None:
            return OCRResult(text="", confidence=0.0, alternatives=[])

        try:
            results = self.ocr.ocr(image, cls=True)
            if not results or not results[0]:
                return OCRResult(text="", confidence=0.0, alternatives=[])

            candidates = []
            for line in results[0]:
                text = line[1][0]
                conf = float(line[1][1])
                cleaned = re.sub(r"[^A-Z0-9]", "", text.upper())
                if cleaned:
                    candidates.append({"text": cleaned, "confidence": conf})

            if not candidates:
                return OCRResult(text="", confidence=0.0, alternatives=[])

            candidates.sort(key=lambda x: x["confidence"], reverse=True)
            best = candidates[0]
            alts = candidates[1:4]

            disagreement = 0.0
            if len(candidates) > 1 and candidates[1]["text"] != best["text"]:
                disagreement = 1.0 - (best["confidence"] - candidates[1]["confidence"])

            adjusted_conf = best["confidence"] * (1.0 - disagreement * 0.3)

            return OCRResult(
                text=best["text"],
                confidence=adjusted_conf,
                alternatives=alts,
            )
        except Exception:
            return OCRResult(text="", confidence=0.0, alternatives=[])
