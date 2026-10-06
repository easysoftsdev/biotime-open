"""Shifts, rosters and holidays endpoints."""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from core.exceptions import NotFoundError
from shifts import schemas
from shifts.models import Holiday, Roster, Shift

router = APIRouter()


# ─── Shifts ───────────────────────────────────────────────────
@router.get("", response_model=list[schemas.ShiftOut])
async def list_shifts(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Shift).where(Shift.tenant_id == current_user.tenant_id))
    return list(result.scalars().all())


@router.post("", response_model=schemas.ShiftOut, status_code=status.HTTP_201_CREATED)
async def create_shift(
    body: schemas.ShiftCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    shift = Shift(tenant_id=current_user.tenant_id, **body.model_dump())
    db.add(shift)
    await db.commit()
    return shift


@router.patch("/{shift_id}", response_model=schemas.ShiftOut)
async def update_shift(
    shift_id: uuid.UUID,
    body: schemas.ShiftCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Shift).where(Shift.id == shift_id, Shift.tenant_id == current_user.tenant_id))
    shift = result.scalar_one_or_none()
    if not shift:
        raise NotFoundError("Shift not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(shift, k, v)
    await db.commit()
    return shift


@router.delete("/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shift(
    shift_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Shift).where(Shift.id == shift_id, Shift.tenant_id == current_user.tenant_id))
    shift = result.scalar_one_or_none()
    if not shift:
        raise NotFoundError("Shift not found")
    await db.delete(shift)
    await db.commit()


# ─── Rosters ──────────────────────────────────────────────────
@router.post("/rosters", response_model=schemas.RosterOut, status_code=status.HTTP_201_CREATED)
async def create_roster(
    body: schemas.RosterCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    roster = Roster(tenant_id=current_user.tenant_id, **body.model_dump())
    db.add(roster)
    await db.commit()
    return roster


@router.post("/rosters/bulk-assign", status_code=status.HTTP_202_ACCEPTED)
async def bulk_assign_roster(
    body: schemas.BulkRosterAssign,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Assign shift to multiple employees at once."""
    for emp_id in body.employee_ids:
        roster = Roster(
            tenant_id=current_user.tenant_id,
            employee_id=emp_id,
            shift_id=body.shift_id,
            effective_from=body.effective_from,
            effective_to=body.effective_to,
            assigned_by=current_user.id,
        )
        db.add(roster)
    await db.commit()
    return {"assigned": len(body.employee_ids)}


# ─── Holidays ─────────────────────────────────────────────────
@router.get("/holidays", response_model=list[schemas.HolidayOut])
async def list_holidays(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Holiday).where(Holiday.tenant_id == current_user.tenant_id))
    return list(result.scalars().all())


@router.post("/holidays", response_model=schemas.HolidayOut, status_code=status.HTTP_201_CREATED)
async def create_holiday(
    body: schemas.HolidayCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    holiday = Holiday(tenant_id=current_user.tenant_id, **body.model_dump())
    db.add(holiday)
    await db.commit()
    return holiday


@router.patch("/holidays/{holiday_id}", response_model=schemas.HolidayOut)
async def update_holiday(
    holiday_id: uuid.UUID,
    body: schemas.HolidayCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    holiday = await db.get(Holiday, holiday_id)
    if not holiday or holiday.tenant_id != current_user.tenant_id:
        raise NotFoundError("Holiday not found")
    for field, val in body.model_dump().items():
        setattr(holiday, field, val)
    db.add(holiday)
    await db.commit()
    return holiday


@router.delete("/holidays/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holiday(
    holiday_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    holiday = await db.get(Holiday, holiday_id)
    if not holiday or holiday.tenant_id != current_user.tenant_id:
        raise NotFoundError("Holiday not found")
    await db.delete(holiday)
    await db.commit()
