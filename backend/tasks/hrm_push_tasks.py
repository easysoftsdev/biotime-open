"""
Celery tasks — HRM push execution and retry.
"""
import uuid

from core.celery_app import celery_app


@celery_app.task(name="tasks.hrm_push_tasks.execute_push_job_task", bind=True, max_retries=5)
def execute_push_job_task(self, job_id: str):
    """Execute a single HRM push job."""
    import asyncio
    from hrm_push.worker import execute_push_job

    async def _run():
        return await execute_push_job(uuid.UUID(job_id))

    try:
        success = asyncio.get_event_loop().run_until_complete(_run())
        return {"job_id": job_id, "success": success}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(name="tasks.hrm_push_tasks.push_attendance_event", bind=True)
def push_attendance_event(self, employee_id: str, event_date: str):
    """
    Route an attendance_calculated event to all active HRM push targets.
    Called by the attendance engine after each record upsert.
    """
    import asyncio
    from datetime import date
    from core.database import AsyncSessionLocal
    from hrm_push.models import HRMPushTarget, HRMPushJob
    from attendance.models import AttendanceRecord
    from employees.models import Employee
    from sqlalchemy import select

    async def _run():
        async with AsyncSessionLocal() as db:
            # Load employee + record
            emp_result = await db.execute(
                select(Employee).where(Employee.id == uuid.UUID(employee_id))
            )
            emp = emp_result.scalar_one_or_none()
            if not emp:
                return

            rec_result = await db.execute(
                select(AttendanceRecord).where(
                    AttendanceRecord.employee_id == uuid.UUID(employee_id),
                    AttendanceRecord.date == date.fromisoformat(event_date),
                )
            )
            rec = rec_result.scalar_one_or_none()
            if not rec:
                return

            # Build base payload
            payload = {
                "employee_id":      str(emp.id),
                "employee_code":    emp.employee_code,
                "employee_name":    f"{emp.first_name} {emp.last_name}",
                "date":             event_date,
                "first_in":         rec.first_in.isoformat() if rec.first_in else None,
                "last_out":         rec.last_out.isoformat() if rec.last_out else None,
                "total_work_minutes": rec.total_work_minutes,
                "late_minutes":     rec.late_minutes,
                "overtime_minutes": rec.overtime_minutes,
                "status":           rec.status,
            }

            # Find active targets subscribed to this event
            targets_result = await db.execute(
                select(HRMPushTarget).where(
                    HRMPushTarget.tenant_id == emp.tenant_id,
                    HRMPushTarget.active == True,  # noqa: E712
                )
            )
            targets = list(targets_result.scalars().all())

            for target in targets:
                subs = target.event_subscriptions or []
                if "attendance_calculated" in subs or "all" in subs:
                    job = HRMPushJob(
                        tenant_id=emp.tenant_id,
                        target_id=target.id,
                        event_type="attendance_calculated",
                        employee_id=emp.id,
                        payload=payload,
                        status="queued",
                    )
                    db.add(job)

            await db.commit()

            # Now fire execute tasks for each created job
            for target in targets:
                pass  # jobs will be picked up by retry_failed_push_jobs

    return asyncio.get_event_loop().run_until_complete(_run())


@celery_app.task(name="tasks.hrm_push_tasks.retry_failed_push_jobs", bind=True)
def retry_failed_push_jobs(self):
    """
    Pick up queued/retrying push jobs and execute them.
    Runs every 5 min via Celery Beat.
    """
    import asyncio
    from datetime import datetime, timezone
    from core.database import AsyncSessionLocal
    from hrm_push.models import HRMPushJob
    from sqlalchemy import select

    async def _run():
        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)
            result = await db.execute(
                select(HRMPushJob)
                .where(HRMPushJob.status.in_(["queued", "retrying"]))
                .where(
                    (HRMPushJob.next_retry_at == None) |  # noqa: E711
                    (HRMPushJob.next_retry_at <= now)
                )
                .limit(50)
            )
            jobs = list(result.scalars().all())
            for job in jobs:
                execute_push_job_task.delay(str(job.id))
            return len(jobs)

    count = asyncio.get_event_loop().run_until_complete(_run())
    return {"dispatched": count}
