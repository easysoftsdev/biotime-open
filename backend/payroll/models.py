"""Payroll domain models."""
import uuid
from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date

from core.models import TenantModel


class PayCode(TenantModel):
    __tablename__ = "pay_codes"
    code:      Mapped[str]   = mapped_column(String(20),  nullable=False)
    name:      Mapped[str]   = mapped_column(String(120), nullable=False)
    type:      Mapped[str]   = mapped_column(String(20),  default="earning")   # earning/deduction/allowance
    rate_type: Mapped[str]   = mapped_column(String(20),  default="fixed")     # fixed/hourly/daily
    rate:      Mapped[float] = mapped_column(Numeric(10,2), default=0)
    taxable:   Mapped[bool]  = mapped_column(Boolean, default=True)


class EmployeeSalary(TenantModel):
    __tablename__ = "employee_salary"
    employee_id:  Mapped[uuid.UUID]      = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    pay_code_id:  Mapped[uuid.UUID]      = mapped_column(UUID(as_uuid=True), ForeignKey("pay_codes.id", ondelete="CASCADE"), nullable=False)
    amount:       Mapped[float]          = mapped_column(Numeric(12,2), nullable=False)
    effective_from: Mapped[date]         = mapped_column(Date, nullable=False)
    effective_to:   Mapped[date | None]    = mapped_column(Date, nullable=True)

    pay_code: Mapped["PayCode"] = relationship()


class PayrollRun(TenantModel):
    __tablename__ = "payroll_runs"
    period_start: Mapped[date]           = mapped_column(Date, nullable=False)
    period_end:   Mapped[date]           = mapped_column(Date, nullable=False)
    status:       Mapped[str]            = mapped_column(String(20), default="draft")
    created_by:   Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), nullable=True)
    notes:        Mapped[str|None]       = mapped_column(Text, nullable=True)

    items: Mapped[list["PayrollItem"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class PayrollItem(TenantModel):
    __tablename__ = "payroll_items"
    payroll_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("payroll_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id:    Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id",    ondelete="CASCADE"), nullable=False)
    pay_code_id:    Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pay_codes.id",    ondelete="CASCADE"), nullable=False)
    amount:         Mapped[float]     = mapped_column(Numeric(12,2), nullable=False)
    hours:          Mapped[float]     = mapped_column(Numeric(8,2), default=0)
    notes:          Mapped[str|None]  = mapped_column(Text, nullable=True)

    run:      Mapped["PayrollRun"] = relationship(back_populates="items")
    pay_code: Mapped["PayCode"]    = relationship()
