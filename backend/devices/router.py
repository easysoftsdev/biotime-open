"""
Device management REST API endpoints.
"""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import CurrentUser, get_current_user
from core.exceptions import NotFoundError
from devices import schemas, service
from devices.models import CommandType

router = APIRouter()


@router.get("", response_model=list[schemas.DeviceOut])
async def list_devices(
    status_filter: str | None = Query(None, alias="status"),
    area_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await service.list_devices(db, current_user.tenant_id, status_filter, area_id)


@router.post("", response_model=schemas.DeviceOut, status_code=status.HTTP_201_CREATED)
async def create_device(
    body: schemas.DeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    device = await service.create_device(
        db,
        tenant_id=current_user.tenant_id,
        serial_number=body.serial_number,
        name=body.name,
        model=body.model,
        timezone=body.timezone,
        area_id=body.area_id,
    )
    await db.commit()
    return device


@router.get("/{device_id}", response_model=schemas.DeviceOut)
async def get_device(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    device = await service.get_device_by_id(db, device_id)
    if not device or device.tenant_id != current_user.tenant_id:
        raise NotFoundError("Device not found")
    return device


@router.patch("/{device_id}", response_model=schemas.DeviceOut)
async def update_device(
    device_id: uuid.UUID,
    body: schemas.DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    device = await service.get_device_by_id(db, device_id)
    if not device or device.tenant_id != current_user.tenant_id:
        raise NotFoundError("Device not found")
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(device, field, val)
    db.add(device)
    await db.commit()
    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    device = await service.get_device_by_id(db, device_id)
    if not device or device.tenant_id != current_user.tenant_id:
        raise NotFoundError("Device not found")
    await db.delete(device)
    await db.commit()


@router.post("/{device_id}/sync", response_model=schemas.SyncTriggerResponse)
async def trigger_sync(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Trigger a manual attendance sync for the device."""
    device = await service.get_device_by_id(db, device_id)
    if not device or device.tenant_id != current_user.tenant_id:
        raise NotFoundError("Device not found")

    from sync.service import create_sync_job
    job = await create_sync_job(db, device, tenant_id=current_user.tenant_id)
    await db.commit()

    # Queue command
    await service.queue_command(
        db, device, CommandType.SYNC_ATTENDANCE,
        payload={"job_id": str(job.id)},
        tenant_id=current_user.tenant_id,
    )
    await db.commit()

    return schemas.SyncTriggerResponse(
        job_id=job.id,
        status=job.status,
        message="Sync job created. Device will upload records on next poll.",
    )


@router.post("/{device_id}/reboot", status_code=status.HTTP_202_ACCEPTED)
async def reboot_device(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    device = await service.get_device_by_id(db, device_id)
    if not device or device.tenant_id != current_user.tenant_id:
        raise NotFoundError("Device not found")
    await service.queue_command(db, device, CommandType.REBOOT, tenant_id=current_user.tenant_id)
    await db.commit()
    return {"message": "Reboot command queued"}


@router.get("/{device_id}/commands", response_model=list[schemas.DeviceCommandOut])
async def list_commands(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    device = await service.get_device_by_id(db, device_id)
    if not device or device.tenant_id != current_user.tenant_id:
        raise NotFoundError("Device not found")
    return await service.get_pending_commands(db, device_id)


@router.get("/{device_id}/capabilities", response_model=schemas.DeviceCapabilityOut)
async def get_capabilities(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    device = await service.get_device_by_id(db, device_id)
    if not device or device.tenant_id != current_user.tenant_id:
        raise NotFoundError("Device not found")
    if not device.capabilities:
        raise NotFoundError("Capabilities not yet resolved for this device")
    return device.capabilities


@router.post("/{device_id}/transfer", status_code=status.HTTP_202_ACCEPTED)
async def transfer_employees(
    device_id: uuid.UUID,
    body: schemas.DeviceTransferRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Transfer employees (with biometrics) to another device."""
    source = await service.get_device_by_id(db, device_id)
    target = await service.get_device_by_id(db, body.target_device_id)
    if not source or source.tenant_id != current_user.tenant_id:
        raise NotFoundError("Source device not found")
    if not target or target.tenant_id != current_user.tenant_id:
        raise NotFoundError("Target device not found")

    from tasks.device_tasks import transfer_employees_task
    transfer_employees_task.delay(
        str(source.id), str(target.id),
        [str(eid) for eid in body.employee_ids],
        body.transfer_all,
    )
    return {"message": "Transfer job queued"}
