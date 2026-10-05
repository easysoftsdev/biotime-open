"""Payroll endpoints."""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from core.exceptions import NotFoundError
from payroll import schemas
from payroll.models import PayCode, PayrollItem, PayrollRun

router = APIRouter()


@router.get("/pay-codes", response_model=list[schemas.PayCodeOut])
async def list_pay_codes(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(PayCode).where(PayCode.tenant_id == current_user.tenant_id))
    return list(result.scalars().all())


@router.post("/pay-codes", response_model=schemas.PayCodeOut, status_code=status.HTTP_201_CREATED)
async def create_pay_code(
    body: schemas.PayCodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    pc = PayCode(tenant_id=current_user.tenant_id, **body.model_dump())
    db.add(pc)
    await db.commit()
    return pc


@router.patch("/pay-codes/{pay_code_id}", response_model=schemas.PayCodeOut)
async def update_pay_code(
    pay_code_id: uuid.UUID,
    body: schemas.PayCodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    pc = await db.get(PayCode, pay_code_id)
    if not pc or pc.tenant_id != current_user.tenant_id:
        raise NotFoundError("Pay code not found")
    for field, val in body.model_dump().items():
        setattr(pc, field, val)
    db.add(pc)
    await db.commit()
    return pc


@router.delete("/pay-codes/{pay_code_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pay_code(
    pay_code_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    pc = await db.get(PayCode, pay_code_id)
    if not pc or pc.tenant_id != current_user.tenant_id:
        raise NotFoundError("Pay code not found")
    await db.delete(pc)
    await db.commit()


@router.get("/runs", response_model=list[schemas.PayrollRunOut])
async def list_runs(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(PayrollRun)
        .where(PayrollRun.tenant_id == current_user.tenant_id)
        .order_by(PayrollRun.period_start.desc())
    )
    return list(result.scalars().all())


@router.post("/runs", response_model=schemas.PayrollRunOut, status_code=status.HTTP_201_CREATED)
async def create_run(
    body: schemas.PayrollRunCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    run = PayrollRun(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        **body.model_dump(),
    )
    db.add(run)
    await db.commit()
    # Trigger payroll calculation async
    from tasks.report_tasks import generate_payroll_run
    generate_payroll_run.delay(str(run.id))
    return run


@router.get("/runs/{run_id}/items", response_model=list[schemas.PayrollItemOut])
async def list_run_items(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(PayrollItem)
        .where(PayrollItem.payroll_run_id == run_id)
    )
    return list(result.scalars().all())


@router.get("/wps-report")
async def wps_report(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate WPS (Wages Protection System) export."""
    from tasks.report_tasks import generate_wps_report
    task = generate_wps_report.delay(str(run_id), str(current_user.tenant_id))
    return {"task_id": task.id, "message": "WPS report generation started"}
