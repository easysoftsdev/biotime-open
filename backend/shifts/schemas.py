"""Shift & Roster schemas."""
import uuid
from datetime import date, time
from pydantic import BaseModel


class ShiftOut(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    start_time: time
    end_time: time
    break_minutes: int
    grace_minutes: int
    overtime_threshold_minutes: int
    cross_day: bool
    color: str | None
    model_config = {"from_attributes": True}


class ShiftCreate(BaseModel):
    name: str
    type: str = "fixed"
    start_time: time
    end_time: time
    break_minutes: int = 0
    grace_minutes: int = 0
    overtime_threshold_minutes: int = 480
    cross_day: bool = False
    color: str | None = None


class RosterOut(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    shift_id: uuid.UUID | None
    effective_from: date
    effective_to: date | None
    model_config = {"from_attributes": True}


class RosterCreate(BaseModel):
    employee_id: uuid.UUID
    shift_id: uuid.UUID
    effective_from: date
    effective_to: date | None = None


class BulkRosterAssign(BaseModel):
    employee_ids: list[uuid.UUID]
    shift_id: uuid.UUID
    effective_from: date
    effective_to: date | None = None


class HolidayOut(BaseModel):
    id: uuid.UUID
    name: str
    date: date
    area_id: uuid.UUID | None
    is_paid: bool
    recurring: bool
    model_config = {"from_attributes": True}


class HolidayCreate(BaseModel):
    name: str
    date: date
    area_id: uuid.UUID | None = None
    is_paid: bool = True
    recurring: bool = False
