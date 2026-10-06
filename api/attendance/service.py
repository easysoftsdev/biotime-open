"""Attendance service — query and manual punch management."""
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from attendance.models import (
    AttendanceRecord, DeviceAttendanceEvent, ManualPunchRequest,
    MANUAL_PUNCH_DEVICE_USER_ID,
)
from core.exceptions import ConflictError, NotFoundError


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


async def list_manual_punches(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    status: str | None = None,
    employee_id: uuid.UUID | None = None,
    limit: int = 100,
) -> list[ManualPunchRequest]:
    """Manual punch requests — newest first, optionally filtered."""
    q = select(ManualPunchRequest).where(
        ManualPunchRequest.tenant_id == tenant_id
    )
    if status:
        q = q.where(ManualPunchRequest.status == status)
    if employee_id:
        q = q.where(ManualPunchRequest.employee_id == employee_id)
    q = q.order_by(ManualPunchRequest.created_at.desc()).limit(limit)
    result = await db.execute(q)
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
    if req.status != "pending":
        raise ConflictError(f"Manual punch request already {req.status}")
    req.status = "approved" if approve else "rejected"
    req.approved_by = approver_id
    req.approved_at = datetime.now(timezone.utc)
    req.rejected_reason = reject_reason
    db.add(req)
    await db.flush()

    # If approved — inject a raw event (device_id stays NULL: no physical device)
    if approve:
        from devices.adms.handler import _fingerprint

        fp = _fingerprint(
            MANUAL_PUNCH_DEVICE_USER_ID, str(req.employee_id), str(req.requested_time)
        )
        existing = await db.execute(
            select(DeviceAttendanceEvent.id).where(
                DeviceAttendanceEvent.tenant_id == req.tenant_id,
                DeviceAttendanceEvent.event_fingerprint == fp,
            )
        )
        if not existing.scalar_one_or_none():
            db.add(
                DeviceAttendanceEvent(
                    tenant_id=req.tenant_id,
                    device_id=None,
                    device_user_id=MANUAL_PUNCH_DEVICE_USER_ID,
                    employee_id=req.employee_id,
                    event_time=req.requested_time,
                    event_time_local=req.requested_time,
                    verify_state=0 if req.punch_type == "in" else 1,
                    event_fingerprint=fp,
                    raw_payload={
                        "source": "manual_punch",
                        "request_id": str(req.id),
                        "approved_by": str(approver_id),
                    },
                )
            )
            await db.flush()

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
