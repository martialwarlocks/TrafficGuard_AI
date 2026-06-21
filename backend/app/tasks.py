import asyncio
import time
from datetime import datetime
from backend.app.celery_app import celery_app


@celery_app.task(name="backend.app.tasks.analyze_image")
def analyze_image_task(image_path: str, camera_id: int | None = None):
    from ml.pipeline.analyzer import TrafficAnalyzer

    analyzer = TrafficAnalyzer()
    start = time.time()
    result = analyzer.analyze(image_path, camera_id=camera_id)
    result["processing_time_ms"] = (time.time() - start) * 1000
    return result


@celery_app.task(name="backend.app.tasks.process_stream_frame")
def process_stream_frame_task(frame_bytes: bytes, camera_id: int):
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(frame_bytes)
        temp_path = f.name

    try:
        from ml.pipeline.analyzer import TrafficAnalyzer
        analyzer = TrafficAnalyzer()
        return analyzer.analyze(temp_path, camera_id=camera_id)
    finally:
        os.unlink(temp_path)


@celery_app.task(name="backend.app.tasks.collect_system_metrics")
def collect_system_metrics():
    import psutil
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend.app.models import SystemMetric
    from backend.app.config import get_settings

    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "")
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        metric = SystemMetric(
            cpu_usage=psutil.cpu_percent(),
            memory_usage=psutil.virtual_memory().percent,
            disk_usage=psutil.disk_usage("/").percent,
            active_cameras=0,
            queue_depth=0,
            requests_per_minute=0,
            error_rate=0,
            recorded_at=datetime.utcnow(),
        )
        session.add(metric)
        session.commit()
    return {"status": "ok"}


@celery_app.task(name="backend.app.tasks.check_model_drift")
def check_model_drift():
    return {"drift_score": 0.05, "status": "stable", "checked_at": datetime.utcnow().isoformat()}


@celery_app.task(name="backend.app.tasks.reindex_violation")
def reindex_violation_task(violation_data: dict):
    from backend.app.services.elasticsearch import es_service

    async def _index():
        await es_service.connect()
        await es_service.index_violation(violation_data)
        await es_service.close()

    asyncio.run(_index())
    return {"status": "indexed"}
