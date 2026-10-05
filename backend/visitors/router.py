"""Visitor management endpoints."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.deps import get_current_user
from core.exceptions import NotFoundError
from visitors.models import Visitor

router = APIRouter()


@router.get("")
async def list_visitors(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(Visitor).where(Visitor.tenant_id == current_user.tenant_id)
        .order_by(Visitor.created_at.desc()).limit(100)
    )
    return list(result.scalars().all())


@router.post("/check-in", status_code=status.HTTP_201_CREATED)
async def check_in(
    name: str, company: str | None = None, purpose: str | None = None,
    host_employee_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    visitor = Visitor(
        tenant_id=current_user.tenant_id,
        name=name, company=company, purpose=purpose,
        host_employee_id=host_employee_id,
        check_in_at=datetime.now(timezone.utc),
        status="checked_in",
    )
    db.add(visitor)
    await db.commit()
    return visitor


@router.post("/{visitor_id}/check-out")
async def check_out(
    visitor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Visitor).where(Visitor.id == visitor_id))
    visitor = result.scalar_one_or_none()
    if not visitor:
        raise NotFoundError("Visitor not found")
    visitor.check_out_at = datetime.now(timezone.utc)
    visitor.status = "checked_out"
    db.add(visitor)
    await db.commit()
    return visitor
