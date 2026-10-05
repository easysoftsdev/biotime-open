"""
Device request / response schemas.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DeviceOut(BaseModel):
    id: uuid.UUID
    serial_number: str
    name: str
    model: str | None
    firmware_version: str | None
    ip_address: str | None
    status: str
    timezone: str
    pending_sync: bool
    last_seen_at: datetime | None
    last_sync_at: datetime | None
    last_successful_sync_at: datetime | None
    last_error: str | None
    tenant_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class DeviceCreate(BaseModel):
    serial_number: str
    name: str
    model: str | None = None
    timezone: str = "UTC"
    area_id: uuid.UUID | None = None


class DeviceUpdate(BaseModel):
    name: str | None = None
    timezone: str | None = None
    area_id: uuid.UUID | None = None
    status: str | None = None


class DeviceCapabilityOut(BaseModel):
    protocol: str
    supports_face: bool
    supports_fingerprint: bool
    supports_palm: bool
    supports_rfid: bool
    supports_qr: bool
    supports_temperature: bool
    max_users: int
    max_transactions: int
    last_capability_sync: datetime | None

    model_config = {"from_attributes": True}


class DeviceCommandOut(BaseModel):
    id: uuid.UUID
    command_type: str
    status: str
    attempts: int
    error: str | None
    scheduled_at: datetime | None
    executed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SyncTriggerResponse(BaseModel):
    job_id: uuid.UUID
    status: str
    message: str


class DeviceTransferRequest(BaseModel):
    target_device_id: uuid.UUID
    employee_ids: list[uuid.UUID] = Field(default_factory=list)
    transfer_all: bool = False
