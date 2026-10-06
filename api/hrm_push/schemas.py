"""HRM Push schemas."""
import uuid
from datetime import datetime
from pydantic import BaseModel


class HRMPushTargetOut(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    base_url: str
    event_subscriptions: list[str]
    active: bool
    retry_max_attempts: int
    created_at: datetime
    model_config = {"from_attributes": True}


class HRMPushTargetCreate(BaseModel):
    name: str
    type: str = "custom"
    base_url: str
    auth_config: dict = {}
    field_map: dict = {}
    event_subscriptions: list[str] = []
    headers: dict = {}
    retry_max_attempts: int = 5
    timeout_seconds: int = 30
    verify_ssl: bool = True


class HRMPushTargetUpdate(BaseModel):
    name: str | None = None
    base_url: str | None = None
    auth_config: dict | None = None
    field_map: dict | None = None
    event_subscriptions: list[str] | None = None
    active: bool | None = None


class PushLogOut(BaseModel):
    id: uuid.UUID
    event_type: str
    employee_id: uuid.UUID | None
    response_status: int | None
    attempt_number: int
    sent_at: datetime | None
    duration_ms: int
    success: bool
    model_config = {"from_attributes": True}


class PushJobOut(BaseModel):
    id: uuid.UUID
    target_id: uuid.UUID
    event_type: str
    employee_id: uuid.UUID | None
    status: str
    attempts: int
    error: str | None
    next_retry_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}
