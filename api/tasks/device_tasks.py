"""
Celery tasks — device health, sync, employee transfer.
"""
import uuid

from core.celery_app import celery_app


@celery_app.task(name="tasks.device_tasks.check_device_health", bind=True, max_retries=1)
def check_device_health(self):
    """Mark devices offline if heartbeat threshold exceeded. Runs every 1 min."""
    import asyncio
    from core.database import AsyncSessionLocal
    from devices.service import mark_offline_devices

    async def _run():
        async with AsyncSessionLocal() as db:
            count = await mark_offline_devices(db)
            await db.commit()
            return count

    count = asyncio.get_event_loop().run_until_complete(_run())
    return {"marked_offline": count}


@celery_app.task(name="tasks.device_tasks.retry_failed_syncs", bind=True)
def retry_failed_syncs(self):
    """Re-queue WAITING_FOR_DEVICE sync commands. Runs every 5 min."""
    import asyncio
    from core.database import AsyncSessionLocal
    from sqlalchemy import select
    from devices.models import DeviceCommand, CommandStatus, DeviceStatus
    from devices.models import Device

    async def _run():
        async with AsyncSessionLocal() as db:
            # Find online devices that have waiting commands
            result = await db.execute(
                select(DeviceCommand)
                .join(Device, Device.id == DeviceCommand.device_id)
                .where(
                    DeviceCommand.status == CommandStatus.WAITING_FOR_DEVICE,
                    Device.status == DeviceStatus.ONLINE,
                    DeviceCommand.attempts < DeviceCommand.max_attempts,
                )
                .limit(100)
            )
            commands = list(result.scalars().all())
            for cmd in commands:
                cmd.status = CommandStatus.QUEUED
                db.add(cmd)
            await db.commit()
            return len(commands)

    count = asyncio.get_event_loop().run_until_complete(_run())
    return {"re_queued": count}


@celery_app.task(name="tasks.device_tasks.transfer_employees_task", bind=True)
def transfer_employees_task(
    self,
    source_device_id: str,
    target_device_id: str,
    employee_ids: list[str],
    transfer_all: bool = False,
):
    """Transfer employees with biometrics from one device to another."""
    import asyncio
    from core.database import AsyncSessionLocal
    from devices.service import get_device_by_id, queue_command
    from devices.models import CommandType
    from employees.models import Employee
    from sqlalchemy import select

    async def _run():
        async with AsyncSessionLocal() as db:
            source = await get_device_by_id(db, uuid.UUID(source_device_id))
            target = await get_device_by_id(db, uuid.UUID(target_device_id))
            if not source or not target:
                return {"error": "Device not found"}

            if transfer_all:
                result = await db.execute(
                    select(Employee).where(Employee.tenant_id == target.tenant_id)
                )
                employees = list(result.scalars().all())
            else:
                result = await db.execute(
                    select(Employee).where(
                        Employee.id.in_([uuid.UUID(eid) for eid in employee_ids])
                    )
                )
                employees = list(result.scalars().all())

            for emp in employees:
                payload = {
                    "pin": emp.device_user_id or emp.employee_code,
                    "name": f"{emp.first_name} {emp.last_name}",
                    "privilege": 0,
                }
                await queue_command(db, target, CommandType.CREATE_USER, payload=payload)

            await db.commit()
            return {"transferred": len(employees)}

    return asyncio.get_event_loop().run_until_complete(_run())
