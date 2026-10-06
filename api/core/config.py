"""
Application settings — loaded from environment variables / .env file.
"""
import json
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


def _split_list(raw: str) -> List[str]:
    """Parse `a,b,c` (documented format) or a JSON array into a list."""
    text = raw.strip()
    if not text:
        return []
    if text.startswith("["):
        parsed = json.loads(text)
        return [str(item).strip() for item in parsed if str(item).strip()]
    return [item.strip() for item in text.split(",") if item.strip()]


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
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

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

    # ─── Parsed helpers (env values are comma-separated) ─────
    @property
    def allowed_hosts(self) -> List[str]:
        return _split_list(self.ALLOWED_HOSTS)

    @property
    def cors_origins(self) -> List[str]:
        return _split_list(self.CORS_ORIGINS)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
