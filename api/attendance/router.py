"""Attendance REST endpoints."""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from attendance import schemas, service
from core.database import get_db
from core.deps import get_current_user

router = APIRouter()


@router.get("", response_model=dict)
async def list_attendance(
    employee_id: uuid.UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    att_status: str | None = Query(None, alias="status"),
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    records, total = await service.list_records(
        db, current_user.tenant_id,
        employee_id, start_date, end_date, att_status, page, page_size,
    )
    return {
        "items": [schemas.AttendanceRecordOut.model_validate(r) for r in records],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/live", response_model=list[schemas.AttendanceEventOut])
async def live_events(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Latest punch events — for live dashboard feed."""
    return await service.get_live_events(db, current_user.tenant_id, limit)


@router.get("/summary")
async def dashboard_summary(
    for_date: date | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    d = for_date or date.today()
    return await service.get_dashboard_summary(db, current_user.tenant_id, d)


@router.get("/manual-punch", response_model=list[schemas.ManualPunchOut])
async def list_manual_punches(
    att_status: str | None = Query(None, alias="status"),
    employee_id: uuid.UUID | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Manual punch requests — pending approvals for the attendance queue."""
    return await service.list_manual_punches(
        db, current_user.tenant_id, att_status, employee_id, limit,
    )


@router.post("/manual-punch", response_model=schemas.ManualPunchOut, status_code=status.HTTP_201_CREATED)
async def create_manual_punch(
    body: schemas.ManualPunchCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    req = await service.create_manual_punch(
        db, current_user.tenant_id,
        body.employee_id, body.requested_time, body.punch_type, body.reason,
    )
    await db.commit()
    return req


@router.put("/manual-punch/{request_id}/approve", response_model=schemas.ManualPunchOut)
async def approve_manual_punch(
    request_id: uuid.UUID,
    approve: bool = True,
    reject_reason: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    req = await service.approve_manual_punch(
        db, request_id, current_user.id, approve, reject_reason
    )
    await db.commit()
    if approve:
        # Enqueue only after the commit so the worker sees the new event
        from tasks.attendance_tasks import process_raw_events
        process_raw_events.delay(None, employee_id=str(req.employee_id))
    return req


@router.post("/recalculate", status_code=status.HTTP_202_ACCEPTED)
async def recalculate(
    body: schemas.RecalculateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Trigger attendance recalculation for a date range."""
    from tasks.attendance_tasks import recalculate_range_task
    recalculate_range_task.delay(
        str(current_user.tenant_id),
        str(body.start_date),
        str(body.end_date),
        str(body.employee_id) if body.employee_id else None,
    )
    return {"message": "Recalculation queued", "range": f"{body.start_date} → {body.end_date}"}
