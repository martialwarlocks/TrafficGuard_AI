from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "TrafficGuard AI"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://trafficguard:trafficguard_secret@localhost:5432/trafficguard"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "trafficguard"
    minio_secret_key: str = "trafficguard_minio_secret"
    minio_bucket: str = "trafficguard-evidence"
    minio_secure: bool = False

    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index: str = "trafficguard"

    jwt_secret_key: str = "change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    yolo_model_path: str = "ml/models/yolov8s.pt"
    mc_dropout_passes: int = 20
    auto_process_threshold: float = 0.85
    human_review_threshold: float = 0.60

    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
