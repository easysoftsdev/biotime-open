"""
Application settings — loaded from environment variables / .env file.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ─── App ──────────────────────────────────────────────────
    SECRET_KEY: str = "change-me"
    DEBUG: bool = False
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # ─── Database ─────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://biotime:biotime@localhost:5432/biotime"

    # ─── Redis / Celery ───────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ─── MinIO / S3 ───────────────────────────────────────────
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_BIOPHOTOS: str = "biophotos"
    MINIO_BUCKET_REPORTS: str = "reports"
    MINIO_BUCKET_BACKUPS: str = "backups"
    MINIO_USE_SSL: bool = False

    # ─── JWT ──────────────────────────────────────────────────
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # ─── First admin ──────────────────────────────────────────
    FIRST_ADMIN_EMAIL: str = "admin@example.com"
    FIRST_ADMIN_PASSWORD: str = "Admin@123456"

    # ─── Device ───────────────────────────────────────────────
    DEVICE_OFFLINE_THRESHOLD_SECONDS: int = 300
    DEVICE_SYNC_RETRY_MAX: int = 3

    # ─── HRM Push ─────────────────────────────────────────────
    HRM_PUSH_MAX_RETRIES: int = 5
    HRM_PUSH_TIMEOUT_SECONDS: int = 30

    # ─── Email ────────────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@example.com"
    SMTP_TLS: bool = True

    # ─── Monitoring ───────────────────────────────────────────
    SENTRY_DSN: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
