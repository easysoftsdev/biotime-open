"""
Device domain models — Device, DeviceModel, DeviceCapability, DeviceCommand.
"""
import uuid
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from datetime import datetime

from core.models import BaseModel, TenantModel


class DeviceStatus(str, PyEnum):
    UNKNOWN  = "unknown"
    ONLINE   = "online"
    OFFLINE  = "offline"
    DISABLED = "disabled"


class CommandStatus(str, PyEnum):
    QUEUED             = "queued"
    SENT               = "sent"
    COMPLETED          = "completed"
    FAILED             = "failed"
    WAITING_FOR_DEVICE = "waiting_for_device"


class CommandType(str, PyEnum):
    CREATE_USER    = "CREATE_USER"
    UPDATE_USER    = "UPDATE_USER"
    DELETE_USER    = "DELETE_USER"
    PUSH_TEMPLATE  = "PUSH_TEMPLATE"
    PULL_TEMPLATE  = "PULL_TEMPLATE"
    SYNC_ATTENDANCE= "SYNC_ATTENDANCE"
    REBOOT         = "REBOOT"
    SET_TIME       = "SET_TIME"
    CLEAR_DATA     = "CLEAR_DATA"
    CUSTOM         = "CUSTOM"


# ─── Device Model Registry ────────────────────────────────────
class DeviceModel(BaseModel):
    """Registry of known ZKTeco device models and their capabilities."""
    __tablename__ = "device_models"

    series: Mapped[str]        = mapped_column(String(80), nullable=False)
    model_code: Mapped[str]    = mapped_column(String(80), unique=True, nullable=False)
    display_name: Mapped[str]  = mapped_column(String(120), nullable=False)
    adms_supported: Mapped[bool]    = mapped_column(Boolean, default=True)
    push_sdk_supported: Mapped[bool]= mapped_column(Boolean, default=False)
    tcp_supported: Mapped[bool]     = mapped_column(Boolean, default=False)
    default_capabilities: Mapped[dict] = mapped_column(JSONB, default=dict)


# ─── Device ───────────────────────────────────────────────────
class Device(TenantModel):
    __tablename__ = "devices"

    serial_number: Mapped[str]  = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str]           = mapped_column(String(120), nullable=False)
    model: Mapped[str | None]   = mapped_column(String(80), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ip_address: Mapped[str | None]       = mapped_column(String(45), nullable=True)
    status: Mapped[str]         = mapped_column(String(20), default=DeviceStatus.UNKNOWN)
    area_id: Mapped[uuid.UUID | None]    = mapped_column(UUID(as_uuid=True), nullable=True)
    timezone: Mapped[str]       = mapped_column(String(60), default="UTC")
    pending_sync: Mapped[bool]  = mapped_column(Boolean, default=False)

    last_seen_at: Mapped[datetime | None]            = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_at: Mapped[datetime | None]            = mapped_column(DateTime(timezone=True), nullable=True)
    last_successful_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_at: Mapped[datetime | None]           = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None]                   = mapped_column(Text, nullable=True)

    # Relationships
    capabilities: Mapped["DeviceCapability | None"] = relationship(
        back_populates="device", uselist=False, cascade="all, delete-orphan"
    )
    commands: Mapped[list["DeviceCommand"]] = relationship(
        back_populates="device", cascade="all, delete-orphan"
    )


# ─── Device Capability ────────────────────────────────────────
class DeviceCapability(BaseModel):
    __tablename__ = "device_capabilities"

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )
    protocol: Mapped[str]       = mapped_column(String(20), default="adms")

    supports_face: Mapped[bool]        = mapped_column(Boolean, default=False)
    supports_fingerprint: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_palm: Mapped[bool]        = mapped_column(Boolean, default=False)
    supports_rfid: Mapped[bool]        = mapped_column(Boolean, default=False)
    supports_qr: Mapped[bool]          = mapped_column(Boolean, default=False)
    supports_temperature: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_mask_detection: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_video_intercom: Mapped[bool] = mapped_column(Boolean, default=False)

    max_users: Mapped[int]        = mapped_column(Integer, default=50000)
    max_faces: Mapped[int]        = mapped_column(Integer, default=50000)
    max_fingerprints: Mapped[int] = mapped_column(Integer, default=3000)
    max_cards: Mapped[int]        = mapped_column(Integer, default=50000)
    max_transactions: Mapped[int] = mapped_column(Integer, default=1000000)

    last_capability_sync: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    device: Mapped["Device"] = relationship(back_populates="capabilities")


# ─── Device Command ───────────────────────────────────────────
class DeviceCommand(TenantModel):
    __tablename__ = "device_commands"

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    command_type: Mapped[str]  = mapped_column(String(40), nullable=False)
    payload: Mapped[dict]      = mapped_column(JSONB, default=dict)
    status: Mapped[str]        = mapped_column(String(30), default=CommandStatus.QUEUED, index=True)
    attempts: Mapped[int]      = mapped_column(Integer, default=0)
    max_attempts: Mapped[int]  = mapped_column(Integer, default=3)
    error: Mapped[str | None]  = mapped_column(Text, nullable=True)
    sync_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[datetime | None]  = mapped_column(DateTime(timezone=True), nullable=True)

    device: Mapped["Device"] = relationship(back_populates="commands")
