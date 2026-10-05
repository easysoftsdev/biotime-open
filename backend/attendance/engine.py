"""
Attendance Engine — processes raw device events into calculated records.

Flow:
  DeviceAttendanceEvent (raw, immutable)
    → resolve employee
    → group by employee + date
    → apply shift rules (late, early-leave, overtime, absent)
    → upsert AttendanceRecord
    → trigger HRM push
"""
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import ColumnElement, literal, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from attendance.models import (
    AttendanceRecord, AttendancePolicy, AttendanceStatus,
    DeviceAttendanceEvent, MANUAL_PUNCH_DEVICE_USER_ID,
)
from employees.service import get_employee_by_device_uid


async def process_device_events(db: AsyncSession, device_id: uuid.UUID) -> int:
    """
    Process all unprocessed raw events for a device.
    Returns number of attendance records updated.
    """
    return await _process_unprocessed(
        db, DeviceAttendanceEvent.device_id == device_id
    )


async def process_employee_events(db: AsyncSession, employee_id: uuid.UUID) -> int:
    """
    Process all unprocessed raw events for one employee — used for manual
    punches, which have no device attached.
    """
    return await _process_unprocessed(
        db, DeviceAttendanceEvent.employee_id == employee_id
    )


async def _process_unprocessed(
    db: AsyncSession, *criteria: ColumnElement[bool]
) -> int:
    # Fetch unprocessed events matching the criteria
    result = await db.execute(
        select(DeviceAttendanceEvent)
        .where(DeviceAttendanceEvent.processed == False, *criteria)  # noqa: E712
        .order_by(DeviceAttendanceEvent.event_time.asc())
    )
    events = list(result.scalars().all())
    if not events:
        return 0

    # Get tenant_id from first event
    tenant_id = events[0].tenant_id

    # Group events by employee + date
    groups: dict[tuple[uuid.UUID, date], list[DeviceAttendanceEvent]] = {}
    for event in events:
        # Resolve employee if not already linked
        if not event.employee_id:
            emp = await get_employee_by_device_uid(db, tenant_id, event.device_user_id)
            if emp:
                event.employee_id = emp.id
                db.add(event)

        if not event.employee_id:
            # Unknown user — mark processed and skip
            event.processed = True
            db.add(event)
            continue

        event_date = event.event_time.date()
        key = (event.employee_id, event_date)
        groups.setdefault(key, []).append(event)

    # Process each group
    updated = 0
    for (employee_id, event_date), day_events in groups.items():
        await _calculate_daily_record(db, employee_id, event_date, day_events, tenant_id)
        # Mark events as processed
        for event in day_events:
            event.processed = True
            db.add(event)
        updated += 1

    await db.flush()
    return updated


async def _calculate_daily_record(
    db: AsyncSession,
    employee_id: uuid.UUID,
    event_date: date,
    events: list[DeviceAttendanceEvent],
    tenant_id: uuid.UUID,
) -> AttendanceRecord:
    """Calculate a single daily attendance record from raw events."""

    # Sort by time
    events = sorted(events, key=lambda e: e.event_time)

    # Any contributed by an admin-approved manual punch?
    is_manual = any(
        e.device_user_id == MANUAL_PUNCH_DEVICE_USER_ID for e in events
    )

    first_in  = events[0].event_time
    last_out  = events[-1].event_time

    # Total work = last_out - first_in (in minutes)
    total_work = int((last_out - first_in).total_seconds() / 60) if last_out > first_in else 0

    # Get applicable policy
    policy = await _get_policy(db, tenant_id, employee_id)

    # Get shift for this employee on this date
    shift = await _get_shift(db, employee_id, event_date)

    late_minutes        = 0
    early_leave_minutes = 0
    overtime_minutes    = 0
    status              = AttendanceStatus.PRESENT

    if shift:
        shift_start = _combine(event_date, shift.start_time)
        shift_end   = _combine(event_date, shift.end_time)

        # Cross-midnight shift
        if shift.cross_day and shift.end_time < shift.start_time:
            shift_end += timedelta(days=1)

        # Late arrival
        grace = policy.late_grace_minutes if policy else 0
        if first_in > shift_start + timedelta(minutes=grace):
            late_minutes = int((first_in - shift_start).total_seconds() / 60) - grace

        # Early leave
        el_grace = policy.early_leave_grace_minutes if policy else 0
        if last_out < shift_end - timedelta(minutes=el_grace):
            early_leave_minutes = int((shift_end - last_out).total_seconds() / 60) - el_grace

        # Overtime
        ot_threshold = policy.overtime_threshold_minutes if policy else 480
        if total_work > ot_threshold:
            overtime_minutes = total_work - ot_threshold

        # Absence check
        absence_threshold = policy.absence_threshold_minutes if policy else 240
        half_day_threshold = policy.half_day_threshold_minutes if policy else 240
        if total_work < absence_threshold:
            status = AttendanceStatus.ABSENT
        elif total_work < half_day_threshold:
            status = AttendanceStatus.HALF_DAY

    # Upsert attendance record
    stmt = pg_insert(AttendanceRecord).values(
        employee_id=employee_id,
        date=event_date,
        tenant_id=tenant_id,
        shift_id=shift.id if shift else None,
        first_in=first_in,
        last_out=last_out,
        total_work_minutes=total_work,
        late_minutes=late_minutes,
        early_leave_minutes=early_leave_minutes,
        overtime_minutes=overtime_minutes,
        status=status,
        is_manual=is_manual,
        calculated_at=datetime.now(timezone.utc),
    ).on_conflict_do_update(
        index_elements=["employee_id", "date"],
        set_={
            "first_in": first_in,
            "last_out": last_out,
            "total_work_minutes": total_work,
            "late_minutes": late_minutes,
            "early_leave_minutes": early_leave_minutes,
            "overtime_minutes": overtime_minutes,
            "status": status,
            # sticky: a later device-only batch must not clear the flag
            "is_manual": or_(AttendanceRecord.is_manual, literal(is_manual)),
            "calculated_at": datetime.now(timezone.utc),
        },
    ).returning(AttendanceRecord)

    result = await db.execute(stmt)
    record = result.scalar_one()

    # Trigger HRM push
    from tasks.hrm_push_tasks import push_attendance_event
    push_attendance_event.delay(str(employee_id), str(event_date))

    return record


def _combine(d: date, t) -> datetime:
    """Combine a date and time into a timezone-aware datetime."""
    return datetime.combine(d, t, tzinfo=timezone.utc)


async def _get_policy(
    db: AsyncSession, tenant_id: uuid.UUID, employee_id: uuid.UUID
) -> AttendancePolicy | None:
    """Get most specific attendance policy for an employee."""
    result = await db.execute(
        select(AttendancePolicy)
        .where(AttendancePolicy.tenant_id == tenant_id)
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _get_shift(db: AsyncSession, employee_id: uuid.UUID, for_date: date):
    """Get the assigned shift for an employee on a given date."""
    try:
        from shifts.models import Roster, Shift
        result = await db.execute(
            select(Shift)
            .join(Roster, Roster.shift_id == Shift.id)
            .where(
                Roster.employee_id == employee_id,
                Roster.effective_from <= for_date,
            )
            .where(
                (Roster.effective_to == None) | (Roster.effective_to >= for_date)  # noqa: E711
            )
            .order_by(Roster.effective_from.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    except Exception:
        return None


async def recalculate_range(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    start_date: date,
    end_date: date,
    employee_id: uuid.UUID | None = None,
) -> int:
    """Recalculate attendance records for a date range."""
    q = (
        select(DeviceAttendanceEvent)
        .where(
            DeviceAttendanceEvent.tenant_id == tenant_id,
            DeviceAttendanceEvent.event_time >= datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc),
            DeviceAttendanceEvent.event_time <= datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc),
        )
    )
    if employee_id:
        q = q.where(DeviceAttendanceEvent.employee_id == employee_id)

    # Reset processed flag to force reprocessing
    result = await db.execute(q)
    events = list(result.scalars().all())
    for e in events:
        e.processed = False
        db.add(e)
    await db.flush()

    # Reprocess by device; manual events (no device) by employee
    device_ids = {e.device_id for e in events if e.device_id is not None}
    manual_employees = {
        e.employee_id for e in events
        if e.device_id is None and e.employee_id is not None
    }
    total = 0
    for did in device_ids:
        total += await process_device_events(db, did)
    for eid in manual_employees:
        total += await process_employee_events(db, eid)
    return total
