"""Leave management endpoints."""
import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from core.exceptions import NotFoundError, ValidationError
from leave import schemas
from leave.models import LeaveBalance, LeaveRequest, LeaveType

router = APIRouter()


# ─── Leave Types ──────────────────────────────────────────────
@router.get("/types", response_model=list[schemas.LeaveTypeOut])
async def list_leave_types(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(LeaveType).where(LeaveType.tenant_id == current_user.tenant_id))
    return list(result.scalars().all())


@router.post("/types", response_model=schemas.LeaveTypeOut, status_code=status.HTTP_201_CREATED)
async def create_leave_type(
    body: schemas.LeaveTypeCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    lt = LeaveType(tenant_id=current_user.tenant_id, **body.model_dump())
    db.add(lt)
    await db.commit()
    return lt


# ─── Leave Balances ───────────────────────────────────────────
@router.get("/balances", response_model=list[schemas.LeaveBalanceOut])
async def list_balances(
    employee_id: uuid.UUID | None = None,
    year: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = select(LeaveBalance).where(LeaveBalance.tenant_id == current_user.tenant_id)
    if employee_id:
        q = q.where(LeaveBalance.employee_id == employee_id)
    if year:
        q = q.where(LeaveBalance.year == year)
    result = await db.execute(q)
    return list(result.scalars().all())


# ─── Leave Requests ───────────────────────────────────────────
@router.get("/requests", response_model=list[schemas.LeaveRequestOut])
async def list_requests(
    employee_id: uuid.UUID | None = None,
    req_status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = select(LeaveRequest).where(LeaveRequest.tenant_id == current_user.tenant_id)
    if employee_id:
        q = q.where(LeaveRequest.employee_id == employee_id)
    if req_status:
        q = q.where(LeaveRequest.status == req_status)
    q = q.order_by(LeaveRequest.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


@router.post("/requests", response_model=schemas.LeaveRequestOut, status_code=status.HTTP_201_CREATED)
async def create_leave_request(
    body: schemas.LeaveRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Calculate days
    delta = (body.end_date - body.start_date).days + 1
    if delta <= 0:
        raise ValidationError("end_date must be after start_date")

    # Check balance
    current_year = body.start_date.year
    bal_result = await db.execute(
        select(LeaveBalance).where(
            LeaveBalance.tenant_id == current_user.tenant_id,
            LeaveBalance.employee_id == body.employee_id,
            LeaveBalance.leave_type_id == body.leave_type_id,
            LeaveBalance.year == current_year,
        )
    )
    balance = bal_result.scalar_one_or_none()
    if balance and balance.balance < delta:
        raise ValidationError(f"Insufficient leave balance. Available: {balance.balance} days")

    req = LeaveRequest(
        tenant_id=current_user.tenant_id,
        days=delta,
        **body.model_dump(),
    )
    db.add(req)
    await db.commit()
    return req


@router.put("/requests/{request_id}/approve", response_model=schemas.LeaveRequestOut)
async def approve_leave_request(
    request_id: uuid.UUID,
    body: schemas.LeaveApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(LeaveRequest).where(
            LeaveRequest.id == request_id,
            LeaveRequest.tenant_id == current_user.tenant_id,
        )
    )
    req = result.scalar_one_or_none()
    if not req:
        raise NotFoundError("Leave request not found")

    req.status = "approved" if body.approve else "rejected"
    req.approved_by = current_user.id
    req.approved_at = datetime.now(timezone.utc)
    req.rejection_reason = body.rejection_reason

    # Deduct balance if approved
    if body.approve:
        bal_result = await db.execute(
            select(LeaveBalance).where(
                LeaveBalance.employee_id == req.employee_id,
                LeaveBalance.leave_type_id == req.leave_type_id,
                LeaveBalance.year == req.start_date.year,
            )
        )
        balance = bal_result.scalar_one_or_none()
        if balance:
            balance.balance -= float(req.days)
            balance.used    += float(req.days)
            db.add(balance)

    db.add(req)
    await db.commit()
    return req
