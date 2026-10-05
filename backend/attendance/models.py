"""
Attendance domain models.
  - DeviceAttendanceEvent : raw immutable punch events from devices
  - AttendanceRecord      : calculated daily record per employee
  - AttendancePolicy      : rules for late/OT/absent calculation
  - ManualPunchRequest    : manual punch with approval workflow
"""
import uuid

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey,
    Integer, Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import TenantModel


class VerifyType(int):
    FINGERPRINT = 1
    FACE        = 2
    CARD        = 4
    PASSWORD    = 8
    QR          = 16
    PALM        = 32


class AttendanceStatus(str):
    PRESENT  = "present"
    ABSENT   = "absent"
    HALF_DAY = "half_day"
    ON_LEAVE = "on_leave"
    HOLIDAY  = "holiday"
    WEEKEND  = "weekend"


# ─── Raw event (immutable) ────────────────────────────────────
class DeviceAttendanceEvent(TenantModel):
    __tablename__ = "device_attendance_events"
    __table_args__ = (
        UniqueConstraint("device_id", "event_fingerprint", name="uq_event_fingerprint"),
    )

    device_id:        Mapped[uuid.UUID]   = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    device_event_id:  Mapped[str|None]    = mapped_column(String(40),  nullable=True)
    device_user_id:   Mapped[str]         = mapped_column(String(20),  nullable=False, index=True)
    employee_id:      Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True)

    event_time:       Mapped[DateTime]    = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    event_time_local: Mapped[DateTime|None] = mapped_column(DateTime(timezone=True), nullable=True)

    verify_type:  Mapped[int|None]  = mapped_column(Integer, nullable=True)
    verify_state: Mapped[int|None]  = mapped_column(Integer, nullable=True)  # 0=in, 1=out, 2=break, 4=OT-in
    work_code:    Mapped[str|None]  = mapped_column(String(20), nullable=True)
    temperature:  Mapped[float|None]= mapped_column(Numeric(5, 2), nullable=True)

    raw_payload:       Mapped[dict] = mapped_column(JSONB, default=dict)
    event_fingerprint: Mapped[str]  = mapped_column(String(64), nullable=False, index=True)
    processed:         Mapped[bool] = mapped_column(Boolean, default=False)


# ─── Calculated attendance record ─────────────────────────────
class AttendanceRecord(TenantModel):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("employee_id", "date", name="uq_attendance_record"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    date:        Mapped[Date]      = mapped_column(Date, nullable=False, index=True)
    shift_id:    Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), nullable=True)

    first_in:  Mapped[DateTime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_out:  Mapped[DateTime|None] = mapped_column(DateTime(timezone=True), nullable=True)

    total_work_minutes:  Mapped[int] = mapped_column(Integer, default=0)
    break_minutes:       Mapped[int] = mapped_column(Integer, default=0)
    late_minutes:        Mapped[int] = mapped_column(Integer, default=0)
    early_leave_minutes: Mapped[int] = mapped_column(Integer, default=0)
    overtime_minutes:    Mapped[int] = mapped_column(Integer, default=0)
    absent_minutes:      Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[str] = mapped_column(String(20), default=AttendanceStatus.PRESENT)

    is_manual:          Mapped[bool]        = mapped_column(Boolean, default=False)
    manually_edited_by: Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), nullable=True)
    manually_edited_at: Mapped[DateTime|None]  = mapped_column(DateTime(timezone=True), nullable=True)
    calculated_at:      Mapped[DateTime|None]  = mapped_column(DateTime(timezone=True), nullable=True)

    notes: Mapped[str|None] = mapped_column(Text, nullable=True)


# ─── Attendance Policy ────────────────────────────────────────
class AttendancePolicy(TenantModel):
    __tablename__ = "attendance_policies"

    name:                         Mapped[str] = mapped_column(String(120), nullable=False)
    late_grace_minutes:           Mapped[int] = mapped_column(Integer, default=0)
    early_leave_grace_minutes:    Mapped[int] = mapped_column(Integer, default=0)
    absence_threshold_minutes:    Mapped[int] = mapped_column(Integer, default=240)
    half_day_threshold_minutes:   Mapped[int] = mapped_column(Integer, default=240)
    overtime_threshold_minutes:   Mapped[int] = mapped_column(Integer, default=480)
    overtime_rule:                Mapped[dict] = mapped_column(JSONB, default=dict)
    applicable_departments:       Mapped[list] = mapped_column(JSONB, default=list)


# ─── Manual Punch Request ─────────────────────────────────────
class ManualPunchRequest(TenantModel):
    __tablename__ = "manual_punch_requests"

    employee_id:    Mapped[uuid.UUID]   = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    requested_time: Mapped[DateTime]    = mapped_column(DateTime(timezone=True), nullable=False)
    punch_type:     Mapped[str]         = mapped_column(String(10), default="in")  # in / out
    reason:         Mapped[str|None]    = mapped_column(Text, nullable=True)
    status:         Mapped[str]         = mapped_column(String(20), default="pending")
    approved_by:    Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), nullable=True)
    approved_at:    Mapped[DateTime|None]  = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_reason:Mapped[str|None]    = mapped_column(Text, nullable=True)
