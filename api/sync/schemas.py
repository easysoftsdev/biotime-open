"""Sync job schemas."""
import uuid
from datetime import datetime
from pydantic import BaseModel


class SyncJobOut(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    type: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    records_received: int
    records_inserted: int
    records_duplicate: int
    records_failed: int
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
