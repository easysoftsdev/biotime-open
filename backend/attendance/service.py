"""Attendance service — query and manual punch management."""
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from attendance.models import (
    AttendanceRecord, DeviceAttendanceEvent, ManualPunchRequest
)
from core.exceptions import NotFoundError


async def list_records(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    employee_id: uuid.UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[AttendanceRecord], int]:
    q = select(AttendanceRecord).where(AttendanceRecord.tenant_id == tenant_id)
    if employee_id:
        q = q.where(AttendanceRecord.employee_id == employee_id)
    if start_date:
        q = q.where(AttendanceRecord.date >= start_date)
    if end_date:
        q = q.where(AttendanceRecord.date <= end_date)
    if status:
        q = q.where(AttendanceRecord.status == status)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    q = q.order_by(AttendanceRecord.date.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def get_live_events(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    limit: int = 50,
) -> list[DeviceAttendanceEvent]:
    """Latest raw punch events — used for live dashboard feed."""
    result = await db.execute(
        select(DeviceAttendanceEvent)
        .where(DeviceAttendanceEvent.tenant_id == tenant_id)
        .order_by(DeviceAttendanceEvent.event_time.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def create_manual_punch(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    employee_id: uuid.UUID,
    requested_time: datetime,
    punch_type: str,
    reason: str | None,
) -> ManualPunchRequest:
    req = ManualPunchRequest(
        tenant_id=tenant_id,
        employee_id=employee_id,
        requested_time=requested_time,
        punch_type=punch_type,
        reason=reason,
    )
    db.add(req)
    await db.flush()
    return req


async def approve_manual_punch(
    db: AsyncSession,
    request_id: uuid.UUID,
    approver_id: uuid.UUID,
    approve: bool,
    reject_reason: str | None = None,
) -> ManualPunchRequest:
    result = await db.execute(
        select(ManualPunchRequest).where(ManualPunchRequest.id == request_id)
    )
    req = result.scalar_one_or_none()
    if not req:
        raise NotFoundError("Manual punch request not found")
    req.status = "approved" if approve else "rejected"
    req.approved_by = approver_id
    req.approved_at = datetime.now(timezone.utc)
    req.rejected_reason = reject_reason
    db.add(req)
    await db.flush()

    # If approved — inject a raw event
    if approve:
        from devices.adms.handler import _fingerprint
        from attendance.models import DeviceAttendanceEvent
        fp = _fingerprint("manual", str(req.employee_id), str(req.requested_time))
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        stmt = pg_insert(DeviceAttendanceEvent).values(
            tenant_id=req.tenant_id,
            device_id=None,
            device_user_id="manual",
            employee_id=req.employee_id,
            event_time=req.requested_time,
            verify_state=0 if req.punch_type == "in" else 1,
            event_fingerprint=fp,
            is_manual=True,
        ).on_conflict_do_nothing()
        await db.execute(stmt)
        # Trigger recalculation
        from tasks.attendance_tasks import process_raw_events
        process_raw_events.delay(None, employee_id=str(req.employee_id))

    return req


async def get_dashboard_summary(db: AsyncSession, tenant_id: uuid.UUID, for_date: date) -> dict:
    """Summary stats for the dashboard."""
    total_q = select(func.count()).where(
        AttendanceRecord.tenant_id == tenant_id,
        AttendanceRecord.date == for_date,
    )
    present_q = total_q.where(AttendanceRecord.status == "present")
    absent_q  = total_q.where(AttendanceRecord.status == "absent")
    late_q    = select(func.count()).where(
        AttendanceRecord.tenant_id == tenant_id,
        AttendanceRecord.date == for_date,
        AttendanceRecord.late_minutes > 0,
    )

    total   = (await db.execute(total_q)).scalar_one()
    present = (await db.execute(present_q)).scalar_one()
    absent  = (await db.execute(absent_q)).scalar_one()
    late    = (await db.execute(late_q)).scalar_one()

    return {
        "date": str(for_date),
        "total_records": total,
        "present": present,
        "absent": absent,
        "late": late,
    }
