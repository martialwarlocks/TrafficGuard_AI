"""Singleton ML analyzer — avoids reloading YOLO on every request."""

_analyzer = None


def reset_analyzer():
    global _analyzer
    _analyzer = None


def get_analyzer():
    global _analyzer
    if _analyzer is None:
        from ml.pipeline.analyzer import TrafficAnalyzer
        from backend.app.config import get_settings
        settings = get_settings()
        _analyzer = TrafficAnalyzer(
            model_path=settings.yolo_model_path,
            mc_passes=settings.mc_dropout_passes,
        )
    return _analyzer
