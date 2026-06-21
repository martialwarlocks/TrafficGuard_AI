import hashlib
import io
import uuid
from datetime import datetime
from minio import Minio
from minio.error import S3Error
from backend.app.config import get_settings

settings = get_settings()


class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.bucket = settings.minio_bucket
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error:
            pass

    def upload_bytes(self, data: bytes, content_type: str = "image/jpeg", prefix: str = "evidence") -> tuple[str, str]:
        object_name = f"{prefix}/{datetime.utcnow().strftime('%Y/%m/%d')}/{uuid.uuid4().hex}.jpg"
        evidence_hash = hashlib.sha256(data).hexdigest()
        self.client.put_object(
            self.bucket,
            object_name,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return object_name, evidence_hash

    def get_presigned_url(self, object_name: str, expires_hours: int = 1) -> str:
        from datetime import timedelta
        return self.client.presigned_get_object(
            self.bucket, object_name, expires=timedelta(hours=expires_hours)
        )

    def verify_integrity(self, object_name: str, expected_hash: str) -> bool:
        try:
            response = self.client.get_object(self.bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return hashlib.sha256(data).hexdigest() == expected_hash
        except S3Error:
            return False


storage_service = StorageService()
