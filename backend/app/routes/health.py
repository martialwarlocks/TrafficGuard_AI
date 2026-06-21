from datetime import datetime
from fastapi import APIRouter
from backend.app.schemas import HealthResponse
from backend.app.config import get_settings

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    db_status = "healthy"
    redis_status = "healthy"
    minio_status = "healthy"
    es_status = "healthy"
    ml_status = "healthy"

    try:
        from sqlalchemy import text
        from backend.app.database import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    try:
        import redis
        r = redis.from_url(settings.redis_url)
        r.ping()
    except Exception:
        redis_status = "unhealthy"

    try:
        from backend.app.services.storage import storage_service
        storage_service.client.bucket_exists(storage_service.bucket)
    except Exception:
        minio_status = "unhealthy"

    overall = "healthy" if all(s == "healthy" for s in [db_status, redis_status]) else "degraded"

    return HealthResponse(
        status=overall,
        version="1.0.0",
        database=db_status,
        redis=redis_status,
        minio=minio_status,
        elasticsearch=es_status,
        ml_pipeline=ml_status,
        timestamp=datetime.utcnow(),
    )
