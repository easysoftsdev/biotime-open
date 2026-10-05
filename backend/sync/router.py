"""
Sync job REST endpoints.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from core.exceptions import NotFoundError
from sync import service
from sync.schemas import SyncJobOut

router = APIRouter()


@router.get("", response_model=list[SyncJobOut])
async def list_sync_jobs(
    device_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await service.list_sync_jobs(db, current_user.tenant_id, device_id)


@router.get("/{job_id}", response_model=SyncJobOut)
async def get_sync_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    job = await service.get_sync_job(db, job_id)
    if not job or job.tenant_id != current_user.tenant_id:
        raise NotFoundError("Sync job not found")
    return job


@router.post("/{job_id}/retry", status_code=202)
async def retry_sync_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    job = await service.get_sync_job(db, job_id)
    if not job or job.tenant_id != current_user.tenant_id:
        raise NotFoundError("Sync job not found")
    job.status = "queued"
    db.add(job)
    await db.commit()
    return {"message": "Sync job re-queued"}
