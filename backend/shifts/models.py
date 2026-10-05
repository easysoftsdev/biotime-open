"""
Shift & Roster domain models.
"""
import uuid
from datetime import time, date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Time
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import TenantModel


class ShiftType(str):
    FIXED    = "fixed"
    FLEXIBLE = "flexible"
    OPEN     = "open"


class Shift(TenantModel):
    __tablename__ = "shifts"

    name:       Mapped[str]  = mapped_column(String(120), nullable=False)
    type:       Mapped[str]  = mapped_column(String(20),  default=ShiftType.FIXED)
    start_time: Mapped[time] = mapped_column(Time,        nullable=False)
    end_time:   Mapped[time] = mapped_column(Time,        nullable=False)

    break_minutes:             Mapped[int]  = mapped_column(Integer, default=0)
    grace_minutes:             Mapped[int]  = mapped_column(Integer, default=0)
    overtime_threshold_minutes:Mapped[int]  = mapped_column(Integer, default=480)
    cross_day:                 Mapped[bool] = mapped_column(Boolean, default=False)
    color:                     Mapped[str|None] = mapped_column(String(10), nullable=True)

    rosters: Mapped[list["Roster"]] = relationship(back_populates="shift")


class ShiftCycle(TenantModel):
    __tablename__ = "shift_cycles"

    name:               Mapped[str] = mapped_column(String(120), nullable=False)
    pattern:            Mapped[dict]= mapped_column(JSONB, default=list)  # [{shift_id, days_offset}]
    cycle_length_days:  Mapped[int] = mapped_column(Integer, default=7)


class Roster(TenantModel):
    __tablename__ = "rosters"

    employee_id:   Mapped[uuid.UUID]      = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    shift_id:      Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), ForeignKey("shifts.id",    ondelete="SET NULL"), nullable=True)
    cycle_id:      Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), ForeignKey("shift_cycles.id", ondelete="SET NULL"), nullable=True)
    effective_from:Mapped[date]           = mapped_column(Date, nullable=False)
    effective_to:  Mapped[date | None]      = mapped_column(Date, nullable=True)
    assigned_by:   Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), nullable=True)

    shift: Mapped["Shift|None"] = relationship(back_populates="rosters")


class Holiday(TenantModel):
    __tablename__ = "holidays"

    name:      Mapped[str]          = mapped_column(String(120), nullable=False)
    date:      Mapped[date]         = mapped_column(Date, nullable=False, index=True)
    area_id:   Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), ForeignKey("areas.id", ondelete="SET NULL"), nullable=True)
    is_paid:   Mapped[bool]         = mapped_column(Boolean, default=True)
    recurring: Mapped[bool]         = mapped_column(Boolean, default=False)
