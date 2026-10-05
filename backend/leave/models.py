"""Leave domain models."""
import uuid
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date

from core.models import TenantModel


class LeaveType(TenantModel):
    __tablename__ = "leave_types"

    name:              Mapped[str]   = mapped_column(String(80),  nullable=False)
    accrual_rate:      Mapped[float] = mapped_column(Numeric(6,2), default=0)
    max_balance:       Mapped[float] = mapped_column(Numeric(6,2), default=30)
    carry_forward:     Mapped[bool]  = mapped_column(Boolean, default=False)
    requires_approval: Mapped[bool]  = mapped_column(Boolean, default=True)
    paid:              Mapped[bool]  = mapped_column(Boolean, default=True)
    color:             Mapped[str|None] = mapped_column(String(10), nullable=True)


class LeaveBalance(TenantModel):
    __tablename__ = "leave_balances"

    employee_id:   Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("leave_types.id", ondelete="CASCADE"), nullable=False)
    balance:       Mapped[float]     = mapped_column(Numeric(8,2), default=0)
    used:          Mapped[float]     = mapped_column(Numeric(8,2), default=0)
    accrued:       Mapped[float]     = mapped_column(Numeric(8,2), default=0)
    year:          Mapped[int]       = mapped_column(Integer, nullable=False)

    leave_type: Mapped["LeaveType"] = relationship()


class LeaveRequest(TenantModel):
    __tablename__ = "leave_requests"

    employee_id:        Mapped[uuid.UUID]      = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_type_id:      Mapped[uuid.UUID]      = mapped_column(UUID(as_uuid=True), ForeignKey("leave_types.id"), nullable=False)
    start_date:         Mapped[date]           = mapped_column(Date, nullable=False)
    end_date:           Mapped[date]           = mapped_column(Date, nullable=False)
    days:               Mapped[float]          = mapped_column(Numeric(5,1), nullable=False)
    reason:             Mapped[str|None]       = mapped_column(Text, nullable=True)
    status:             Mapped[str]            = mapped_column(String(20), default="pending")
    current_approver_id:Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), nullable=True)
    approval_level:     Mapped[int]            = mapped_column(Integer, default=1)
    approved_by:        Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), nullable=True)
    approved_at:        Mapped[datetime | None]  = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason:   Mapped[str|None]       = mapped_column(Text, nullable=True)

    leave_type: Mapped["LeaveType"] = relationship()
