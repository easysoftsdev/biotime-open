"""Leave schemas."""
import uuid
from datetime import date, datetime
from pydantic import BaseModel


class LeaveTypeOut(BaseModel):
    id: uuid.UUID
    name: str
    accrual_rate: float
    max_balance: float
    carry_forward: bool
    requires_approval: bool
    paid: bool
    color: str | None
    model_config = {"from_attributes": True}


class LeaveTypeCreate(BaseModel):
    name: str
    accrual_rate: float = 0
    max_balance: float = 30
    carry_forward: bool = False
    requires_approval: bool = True
    paid: bool = True
    color: str | None = None


class LeaveBalanceOut(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    leave_type_id: uuid.UUID
    balance: float
    used: float
    accrued: float
    year: int
    model_config = {"from_attributes": True}


class LeaveRequestCreate(BaseModel):
    employee_id: uuid.UUID
    leave_type_id: uuid.UUID
    start_date: date
    end_date: date
    reason: str | None = None


class LeaveRequestOut(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    leave_type_id: uuid.UUID
    start_date: date
    end_date: date
    days: float
    reason: str | None
    status: str
    approval_level: int
    approved_by: uuid.UUID | None
    approved_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}


class LeaveApprovalRequest(BaseModel):
    approve: bool
    rejection_reason: str | None = None
