"""
Sync job service.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sync.models import SyncJob


async def create_sync_job(db: AsyncSession, device, tenant_id: uuid.UUID) -> SyncJob:
    job = SyncJob(
        device_id=device.id,
        tenant_id=tenant_id,
        type="attendance",
        status="queued",
    )
    db.add(job)
    await db.flush()
    return job


async def get_sync_job(db: AsyncSession, job_id: uuid.UUID) -> SyncJob | None:
    result = await db.execute(select(SyncJob).where(SyncJob.id == job_id))
    return result.scalar_one_or_none()


async def list_sync_jobs(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    device_id: uuid.UUID | None = None,
    limit: int = 50,
) -> list[SyncJob]:
    q = select(SyncJob).where(SyncJob.tenant_id == tenant_id)
    if device_id:
        q = q.where(SyncJob.device_id == device_id)
    q = q.order_by(SyncJob.created_at.desc()).limit(limit)
    result = await db.execute(q)
    return list(result.scalars().all())


async def complete_sync_job(
    db: AsyncSession,
    job: SyncJob,
    received: int,
    inserted: int,
    duplicate: int,
    failed: int,
) -> None:
    job.status = "completed"
    job.completed_at = datetime.now(timezone.utc)
    job.records_received  = received
    job.records_inserted  = inserted
    job.records_duplicate = duplicate
    job.records_failed    = failed
    db.add(job)
    await db.flush()


async def fail_sync_job(db: AsyncSession, job: SyncJob, error: str) -> None:
    job.status = "failed"
    job.completed_at = datetime.now(timezone.utc)
    job.error_message = error
    db.add(job)
    await db.flush()
