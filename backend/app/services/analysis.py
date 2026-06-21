import base64
import cv2
import numpy as np
from backend.app.services.storage import storage_service


def encode_image_b64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def store_analysis_images(content: bytes, result: dict) -> dict:
    """Upload original, enhanced, and annotated images. Returns paths and URLs."""
    import cv2
    import numpy as np

    original_path, evidence_hash = storage_service.upload_bytes(content, prefix="evidence")

    enhanced_path = None
    annotated_path = None

    if result.get("enhanced_image") is not None:
        enhanced_bytes = _encode_cv_image(result["enhanced_image"])
        enhanced_path, _ = storage_service.upload_bytes(enhanced_bytes, prefix="enhanced")

    if result.get("annotated_image") is not None:
        annotated_bytes = _encode_cv_image(result["annotated_image"])
        annotated_path, _ = storage_service.upload_bytes(annotated_bytes, prefix="annotated")

    return {
        "original_path": original_path,
        "enhanced_path": enhanced_path,
        "annotated_path": annotated_path,
        "evidence_hash": evidence_hash,
        "original_url": storage_service.get_presigned_url(original_path, expires_hours=24),
        "enhanced_url": storage_service.get_presigned_url(enhanced_path, expires_hours=24) if enhanced_path else None,
        "annotated_url": storage_service.get_presigned_url(annotated_path, expires_hours=24) if annotated_path else None,
    }


def _encode_cv_image(image: np.ndarray) -> bytes:
    _, buf = cv2.imencode(".jpg", image)
    return buf.tobytes()


def image_urls_for_evidence(evidence) -> dict:
    urls = {}
    if evidence.original_image_path:
        urls["original_url"] = storage_service.get_presigned_url(evidence.original_image_path, expires_hours=24)
    if evidence.enhanced_image_path:
        urls["enhanced_url"] = storage_service.get_presigned_url(evidence.enhanced_image_path, expires_hours=24)
    if evidence.annotated_image_path:
        urls["annotated_url"] = storage_service.get_presigned_url(evidence.annotated_image_path, expires_hours=24)
    return urls
