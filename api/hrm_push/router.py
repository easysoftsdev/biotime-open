"""HRM Push endpoints."""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from core.exceptions import NotFoundError
from hrm_push import schemas
from hrm_push.models import HRMPushJob, HRMPushTarget, PushLog

router = APIRouter()


@router.get("/targets", response_model=list[schemas.HRMPushTargetOut])
async def list_targets(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(HRMPushTarget).where(HRMPushTarget.tenant_id == current_user.tenant_id)
    )
    return list(result.scalars().all())


@router.post("/targets", response_model=schemas.HRMPushTargetOut, status_code=status.HTTP_201_CREATED)
async def create_target(
    body: schemas.HRMPushTargetCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    target = HRMPushTarget(tenant_id=current_user.tenant_id, **body.model_dump())
    db.add(target)
    await db.commit()
    return target


@router.patch("/targets/{target_id}", response_model=schemas.HRMPushTargetOut)
async def update_target(
    target_id: uuid.UUID,
    body: schemas.HRMPushTargetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(HRMPushTarget).where(
            HRMPushTarget.id == target_id,
            HRMPushTarget.tenant_id == current_user.tenant_id,
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise NotFoundError("Push target not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(target, k, v)
    db.add(target)
    await db.commit()
    return target


@router.delete("/targets/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(
    target_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(HRMPushTarget).where(
            HRMPushTarget.id == target_id,
            HRMPushTarget.tenant_id == current_user.tenant_id,
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise NotFoundError("Push target not found")
    await db.delete(target)
    await db.commit()


@router.post("/targets/{target_id}/test", status_code=status.HTTP_202_ACCEPTED)
async def test_target(
    target_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Send a sample test payload to the target HRM."""
    result = await db.execute(
        select(HRMPushTarget).where(
            HRMPushTarget.id == target_id,
            HRMPushTarget.tenant_id == current_user.tenant_id,
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise NotFoundError("Push target not found")

    # Create a test job
    sample_payload = {
        "employee_code": "TEST001",
        "employee_name": "Test Employee",
        "punch_time": "2024-01-15 08:30:00",
        "punch_type": "in",
        "device_serial": "TEST_DEVICE",
        "source": "BioTime Open — test push",
    }
    job = HRMPushJob(
        tenant_id=current_user.tenant_id,
        target_id=target.id,
        event_type="test",
        payload=sample_payload,
        status="queued",
    )
    db.add(job)
    await db.commit()

    from tasks.hrm_push_tasks import execute_push_job_task
    execute_push_job_task.delay(str(job.id))
    return {"job_id": str(job.id), "message": "Test push queued"}


@router.get("/targets/{target_id}/logs", response_model=list[schemas.PushLogOut])
async def target_logs(
    target_id: uuid.UUID,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(PushLog)
        .where(PushLog.target_id == target_id)
        .order_by(PushLog.sent_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/jobs", response_model=list[schemas.PushJobOut])
async def list_jobs(
    push_status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = select(HRMPushJob).where(HRMPushJob.tenant_id == current_user.tenant_id)
    if push_status:
        q = q.where(HRMPushJob.status == push_status)
    q = q.order_by(HRMPushJob.created_at.desc()).limit(200)
    result = await db.execute(q)
    return list(result.scalars().all())


@router.post("/jobs/{job_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(HRMPushJob).where(
            HRMPushJob.id == job_id,
            HRMPushJob.tenant_id == current_user.tenant_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Push job not found")
    job.status = "queued"
    job.next_retry_at = None
    db.add(job)
    await db.commit()

    from tasks.hrm_push_tasks import execute_push_job_task
    execute_push_job_task.delay(str(job.id))
    return {"message": "Job re-queued"}
