"""
MinIO / S3 file storage helper.
"""
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error

from core.config import settings

_client: Minio | None = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        _ensure_buckets(_client)
    return _client


def _ensure_buckets(client: Minio) -> None:
    for bucket in [
        settings.MINIO_BUCKET_BIOPHOTOS,
        settings.MINIO_BUCKET_REPORTS,
        settings.MINIO_BUCKET_BACKUPS,
    ]:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)


def upload_file(bucket: str, object_name: str, data: BinaryIO, length: int, content_type: str = "application/octet-stream") -> str:
    client = get_minio_client()
    client.put_object(bucket, object_name, data, length, content_type=content_type)
    return f"{settings.MINIO_ENDPOINT}/{bucket}/{object_name}"


def get_presigned_url(bucket: str, object_name: str, expires_seconds: int = 3600) -> str:
    from datetime import timedelta
    client = get_minio_client()
    return client.presigned_get_object(bucket, object_name, expires=timedelta(seconds=expires_seconds))


def delete_file(bucket: str, object_name: str) -> None:
    client = get_minio_client()
    try:
        client.remove_object(bucket, object_name)
    except S3Error:
        pass
