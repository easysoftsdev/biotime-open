"""Reports endpoints."""
from datetime import date
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.deps import get_current_user

router = APIRouter()


@router.get("/attendance")
async def attendance_report(
    start_date: date, end_date: date,
    department_id: uuid.UUID | None = None,
    employee_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from tasks.report_tasks import generate_attendance_report
    task = generate_attendance_report.delay(
        str(current_user.tenant_id), str(start_date), str(end_date),
        str(department_id) if department_id else None,
        str(employee_id) if employee_id else None,
    )
    return {"task_id": task.id, "message": "Report generation started"}


@router.get("/device-health")
async def device_health_report(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from sqlalchemy import select, func
    from devices.models import Device
    result = await db.execute(
        select(Device.status, func.count(Device.id).label("count"))
        .where(Device.tenant_id == current_user.tenant_id)
        .group_by(Device.status)
    )
    return {row.status: row.count for row in result}


@router.get("/hrm-push")
async def hrm_push_report(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from sqlalchemy import select, func
    from hrm_push.models import HRMPushJob
    result = await db.execute(
        select(HRMPushJob.status, func.count(HRMPushJob.id).label("count"))
        .where(HRMPushJob.tenant_id == current_user.tenant_id)
        .group_by(HRMPushJob.status)
    )
    return {row.status: row.count for row in result}
