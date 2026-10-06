"""Payroll schemas."""
import uuid
from datetime import date, datetime
from pydantic import BaseModel


class PayCodeOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    type: str
    rate_type: str
    rate: float
    taxable: bool
    model_config = {"from_attributes": True}


class PayCodeCreate(BaseModel):
    code: str
    name: str
    type: str = "earning"
    rate_type: str = "fixed"
    rate: float = 0
    taxable: bool = True


class PayrollItemOut(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    pay_code_id: uuid.UUID
    amount: float
    hours: float
    notes: str | None
    model_config = {"from_attributes": True}


class PayrollRunOut(BaseModel):
    id: uuid.UUID
    period_start: date
    period_end: date
    status: str
    created_at: datetime
    notes: str | None
    model_config = {"from_attributes": True}


class PayrollRunCreate(BaseModel):
    period_start: date
    period_end: date
    notes: str | None = None
