"""
Celery tasks — attendance processing and recalculation.
"""
import uuid

from core.celery_app import celery_app


@celery_app.task(name="tasks.attendance_tasks.process_raw_events", bind=True, max_retries=3)
def process_raw_events(self, device_id: str | None, employee_id: str | None = None):
    """
    Process unprocessed raw attendance events into calculated records.
    Called after ADMS push or manual punch approval.
    """
    import asyncio
    from core.database import AsyncSessionLocal
    from attendance.engine import process_device_events, process_employee_events

    async def _run():
        async with AsyncSessionLocal() as db:
            if device_id:
                count = await process_device_events(db, uuid.UUID(device_id))
                await db.commit()
                return {"processed": count, "device_id": device_id}
            if employee_id:
                # Manual punches are enqueued with no device — process by employee
                count = await process_employee_events(db, uuid.UUID(employee_id))
                await db.commit()
                return {"processed": count, "employee_id": employee_id}
            return {"processed": 0}

    try:
        return asyncio.get_event_loop().run_until_complete(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="tasks.attendance_tasks.nightly_recalculate", bind=True)
def nightly_recalculate(self):
    """
    Nightly recalculation of yesterday's attendance for all tenants.
    Catches any records that were missed during the day.
    """
    import asyncio
    from datetime import date, timedelta
    from core.database import AsyncSessionLocal
    from attendance.engine import recalculate_range
    from sqlalchemy import select
    from core.auth.models import Tenant

    yesterday = date.today() - timedelta(days=1)

    async def _run():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Tenant).where(Tenant.is_active == True))  # noqa: E712
            tenants = list(result.scalars().all())
            total = 0
            for tenant in tenants:
                count = await recalculate_range(db, tenant.id, yesterday, yesterday)
                await db.commit()
                total += count
            return {"date": str(yesterday), "tenants": len(tenants), "records": total}

    return asyncio.get_event_loop().run_until_complete(_run())


@celery_app.task(name="tasks.attendance_tasks.recalculate_range_task", bind=True)
def recalculate_range_task(
    self,
    tenant_id: str,
    start_date: str,
    end_date: str,
    employee_id: str | None = None,
):
    """Recalculate attendance for a specific date range (triggered by admin)."""
    import asyncio
    from datetime import date
    from core.database import AsyncSessionLocal
    from attendance.engine import recalculate_range

    async def _run():
        async with AsyncSessionLocal() as db:
            count = await recalculate_range(
                db,
                uuid.UUID(tenant_id),
                date.fromisoformat(start_date),
                date.fromisoformat(end_date),
                uuid.UUID(employee_id) if employee_id else None,
            )
            await db.commit()
            return {"records_processed": count}

    return asyncio.get_event_loop().run_until_complete(_run())
