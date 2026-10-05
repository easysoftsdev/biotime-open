"""
Device service — CRUD, capability resolver, health checks.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.config import settings
from devices.models import (
    Device, DeviceCapability, DeviceCommand, DeviceModel,
    DeviceStatus, CommandStatus,
)


# ─── Helpers ──────────────────────────────────────────────────
def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─── Device CRUD ──────────────────────────────────────────────
async def get_device_by_serial(db: AsyncSession, serial: str) -> Device | None:
    result = await db.execute(
        select(Device)
        .where(Device.serial_number == serial)
        .options(selectinload(Device.capabilities))
    )
    return result.scalar_one_or_none()


async def get_device_by_id(db: AsyncSession, device_id: uuid.UUID) -> Device | None:
    result = await db.execute(
        select(Device)
        .where(Device.id == device_id)
        .options(selectinload(Device.capabilities))
    )
    return result.scalar_one_or_none()


async def list_devices(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    status: str | None = None,
    area_id: uuid.UUID | None = None,
) -> list[Device]:
    q = select(Device).where(Device.tenant_id == tenant_id)
    if status:
        q = q.where(Device.status == status)
    if area_id:
        q = q.where(Device.area_id == area_id)
    q = q.options(selectinload(Device.capabilities))
    result = await db.execute(q)
    return list(result.scalars().all())


async def create_device(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    serial_number: str,
    name: str,
    model: str | None = None,
    timezone: str = "UTC",
    area_id: uuid.UUID | None = None,
) -> Device:
    device = Device(
        tenant_id=tenant_id,
        serial_number=serial_number,
        name=name or serial_number,
        model=model,
        timezone=timezone,
        area_id=area_id,
        status=DeviceStatus.UNKNOWN,
    )
    db.add(device)
    await db.flush()
    return device


async def update_device_heartbeat(db: AsyncSession, device: Device) -> None:
    device.last_seen_at = utcnow()
    if device.status in (DeviceStatus.UNKNOWN, DeviceStatus.OFFLINE):
        device.status = DeviceStatus.ONLINE
    db.add(device)
    await db.flush()


async def mark_offline_devices(db: AsyncSession) -> int:
    """Called by Celery beat every minute."""
    from datetime import timedelta
    threshold = utcnow() - timedelta(seconds=settings.DEVICE_OFFLINE_THRESHOLD_SECONDS)
    result = await db.execute(
        update(Device)
        .where(Device.status == DeviceStatus.ONLINE)
        .where(Device.last_seen_at < threshold)
        .values(status=DeviceStatus.OFFLINE)
        .returning(Device.id)
    )
    ids = result.fetchall()
    await db.flush()
    return len(ids)


# ─── Capability Resolver ──────────────────────────────────────
async def resolve_capabilities(
    db: AsyncSession,
    device: Device,
    model_hint: str | None = None,
    firmware: str | None = None,
) -> DeviceCapability:
    """
    Resolve device capabilities from model registry.
    Resolution order:
      1. Exact model_code match
      2. Series match
      3. Generic ADMS fallback
    """
    model_code = model_hint or device.model or ""

    # 1. Exact match
    result = await db.execute(
        select(DeviceModel).where(DeviceModel.model_code == model_code)
    )
    device_model = result.scalar_one_or_none()

    # 2. Series match (partial)
    if not device_model and model_code:
        result = await db.execute(
            select(DeviceModel).where(DeviceModel.model_code.ilike(f"%{model_code[:4]}%"))
        )
        device_model = result.scalar_one_or_none()

    # 3. Generic fallback
    if not device_model:
        result = await db.execute(
            select(DeviceModel).where(DeviceModel.model_code == "GENERIC_ADMS")
        )
        device_model = result.scalar_one_or_none()

    caps_data = device_model.default_capabilities if device_model else {}

    # Upsert capability record (explicit SELECT — lazy loading is not
    # available in the async session outside of an await)
    cap_result = await db.execute(
        select(DeviceCapability).where(DeviceCapability.device_id == device.id)
    )
    cap = cap_result.scalar_one_or_none()
    if cap is None:
        cap = DeviceCapability(device_id=device.id)

    cap.protocol = "push_sdk" if (device_model and device_model.push_sdk_supported) else "adms"
    cap.supports_face        = caps_data.get("supports_face", True)
    cap.supports_fingerprint = caps_data.get("supports_fingerprint", False)
    cap.supports_palm        = caps_data.get("supports_palm", False)
    cap.supports_rfid        = caps_data.get("supports_rfid", False)
    cap.supports_qr          = caps_data.get("supports_qr", False)
    cap.supports_temperature = caps_data.get("supports_temperature", False)
    cap.max_users            = caps_data.get("max_users", 50000)
    cap.max_transactions     = caps_data.get("max_transactions", 1000000)
    cap.last_capability_sync = utcnow()

    db.add(cap)
    await db.flush()
    return cap


# ─── Command Queue ────────────────────────────────────────────
async def queue_command(
    db: AsyncSession,
    device: Device,
    command_type: str,
    payload: dict | None = None,
    tenant_id: uuid.UUID | None = None,
) -> DeviceCommand:
    cmd = DeviceCommand(
        device_id=device.id,
        tenant_id=tenant_id or device.tenant_id,
        command_type=command_type,
        payload=payload or {},
        status=(
            CommandStatus.QUEUED
            if device.status == DeviceStatus.ONLINE
            else CommandStatus.WAITING_FOR_DEVICE
        ),
    )
    db.add(cmd)
    await db.flush()
    return cmd


async def get_pending_commands(db: AsyncSession, device_id: uuid.UUID) -> list[DeviceCommand]:
    result = await db.execute(
        select(DeviceCommand)
        .where(DeviceCommand.device_id == device_id)
        .where(DeviceCommand.status.in_([
            CommandStatus.QUEUED, CommandStatus.WAITING_FOR_DEVICE
        ]))
        .order_by(DeviceCommand.created_at.asc())
    )
    return list(result.scalars().all())


async def acknowledge_command(
    db: AsyncSession, cmd_id: uuid.UUID, success: bool, error: str | None = None
) -> None:
    result = await db.execute(select(DeviceCommand).where(DeviceCommand.id == cmd_id))
    cmd = result.scalar_one_or_none()
    if cmd:
        cmd.status = CommandStatus.COMPLETED if success else CommandStatus.FAILED
        cmd.executed_at = utcnow()
        cmd.error = error
        db.add(cmd)
        await db.flush()
