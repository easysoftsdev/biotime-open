"""Attendance schemas."""
import uuid
from datetime import date, datetime
from pydantic import BaseModel


class AttendanceRecordOut(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    date: date
    shift_id: uuid.UUID | None
    first_in: datetime | None
    last_out: datetime | None
    total_work_minutes: int
    late_minutes: int
    early_leave_minutes: int
    overtime_minutes: int
    status: str
    is_manual: bool
    calculated_at: datetime | None
    notes: str | None
    model_config = {"from_attributes": True}


class AttendanceEventOut(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID | None
    device_user_id: str
    employee_id: uuid.UUID | None
    event_time: datetime
    verify_type: int | None
    verify_state: int | None
    work_code: str | None
    temperature: float | None
    processed: bool
    model_config = {"from_attributes": True}


class ManualPunchCreate(BaseModel):
    employee_id: uuid.UUID
    requested_time: datetime
    punch_type: str = "in"
    reason: str | None = None


class ManualPunchOut(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    requested_time: datetime
    punch_type: str
    reason: str | None
    status: str
    approved_by: uuid.UUID | None
    approved_at: datetime | None
    rejected_reason: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class RecalculateRequest(BaseModel):
    start_date: date
    end_date: date
    employee_id: uuid.UUID | None = None


class AttendanceFilterParams(BaseModel):
    employee_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = None
    page: int = 1
    page_size: int = 50
