"""
Sync job models — track every sync operation per device.
"""
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import TenantModel


class SyncJobStatus(str):
    QUEUED             = "queued"
    RUNNING            = "running"
    WAITING_FOR_DEVICE = "waiting_for_device"
    COMPLETED          = "completed"
    FAILED             = "failed"


class SyncJob(TenantModel):
    __tablename__ = "sync_jobs"

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    type: Mapped[str]   = mapped_column(String(40), default="attendance")
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)

    started_at: Mapped[DateTime | None]   = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    records_received: Mapped[int]  = mapped_column(Integer, default=0)
    records_inserted: Mapped[int]  = mapped_column(Integer, default=0)
    records_duplicate: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int]    = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
