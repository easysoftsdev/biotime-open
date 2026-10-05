"""
ADMS Protocol Handler.

ZKTeco devices communicate with:
  GET  /iclock/cdata       — handshake, device sends serial number
  POST /iclock/cdata       — device uploads attendance records
  GET  /iclock/getrequest  — device polls for pending commands
  POST /iclock/devicecmd   — device acknowledges command execution
  GET  /iclock/ping        — heartbeat

Reference: ZKTeco ADMS Communication Protocol v2.2
"""
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qs

from sqlalchemy.ext.asyncio import AsyncSession

from devices.models import DeviceStatus
from devices.service import (
    create_device,
    get_device_by_serial,
    get_pending_commands,
    resolve_capabilities,
    update_device_heartbeat,
    acknowledge_command,
)


def _fingerprint(serial: str, uid: str, event_time: str) -> str:
    """Unique fingerprint for deduplication of attendance events."""
    raw = f"{serial}:{uid}:{event_time}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _parse_adms_time(value: str) -> datetime | None:
    """Parse ZKTeco datetime format: 2024-01-15 08:30:00"""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(value.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


async def handle_handshake(
    db: AsyncSession,
    serial_number: str,
    firmware: str | None,
    model: str | None,
    language: str | None,
    tenant_id: uuid.UUID,
) -> str:
    """
    Handle GET /iclock/cdata — device handshake.
    Creates or retrieves the device and returns config response.
    """
    device = await get_device_by_serial(db, serial_number)

    if not device:
        # Auto-register new device
        device = await create_device(
            db,
            tenant_id=tenant_id,
            serial_number=serial_number,
            name=f"Device-{serial_number[-6:]}",
            model=model,
        )
        await resolve_capabilities(db, device, model_hint=model, firmware=firmware)

    # Update heartbeat + firmware info
    if firmware:
        device.firmware_version = firmware
    if model and not device.model:
        device.model = model
    await update_device_heartbeat(db, device)
    await db.commit()

    # ADMS handshake response format
    server_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"GET OPTION FROM:{serial_number}\n"
        f"ATTLOGStamp=None\n"
        f"OPERLOGStamp=9999\n"
        f"ATTPHOTOStamp=None\n"
        f"ErrorDelay=30\n"
        f"Delay=10\n"
        f"TransTimes=00:00;14:05\n"
        f"TransInterval=1\n"
        f"TransFlag=TransData AttLog\n"
        f"TimeZone=8\n"
        f"Realtime=1\n"
        f"Encrypt=None\n"
        f"ServerVer=2.4.1 {server_time}\n"
        f"PushOptionsFlag=1\n"
    )


async def handle_attendance_upload(
    db: AsyncSession,
    serial_number: str,
    raw_body: str,
    tenant_id: uuid.UUID,
) -> dict[str, int]:
    """
    Handle POST /iclock/cdata — device uploads attendance records.

    Expected body format (one record per line):
    ATTLOG\tUID\tTimestamp\tStatus\tVerify\tWorkCode\tReserved\n
    """
    device = await get_device_by_serial(db, serial_number)
    if not device:
        return {"received": 0, "inserted": 0}

    await update_device_heartbeat(db, device)

    lines = [l.strip() for l in raw_body.splitlines() if l.strip()]
    received = 0
    inserted = 0

    for line in lines:
        if not line.startswith("ATTLOG"):
            continue

        parts = line.split("\t")
        if len(parts) < 3:
            continue

        received += 1
        # parts: ATTLOG  uid  datetime  status  verify  workcode  reserved
        uid        = parts[1] if len(parts) > 1 else ""
        event_time = parts[2] if len(parts) > 2 else ""
        status     = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
        verify     = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
        work_code  = parts[5] if len(parts) > 5 else ""

        parsed_time = _parse_adms_time(event_time)
        if not parsed_time:
            continue

        fp = _fingerprint(serial_number, uid, event_time)
        saved = await _save_raw_event(
            db,
            device_id=device.id,
            device_user_id=uid,
            event_time=parsed_time,
            verify_type=verify,
            verify_state=status,
            work_code=work_code,
            raw_payload={"line": line},
            event_fingerprint=fp,
            tenant_id=tenant_id,
        )
        if saved:
            inserted += 1

    device.last_sync_at = datetime.now(timezone.utc)
    if inserted > 0:
        device.last_successful_sync_at = datetime.now(timezone.utc)
    db.add(device)
    await db.commit()

    # Trigger async attendance processing
    if inserted > 0:
        from tasks.attendance_tasks import process_raw_events
        process_raw_events.delay(str(device.id))

    return {"received": received, "inserted": inserted, "duplicate": received - inserted}


async def _save_raw_event(
    db: AsyncSession,
    device_id: uuid.UUID,
    device_user_id: str,
    event_time: datetime,
    verify_type: int,
    verify_state: int,
    work_code: str,
    raw_payload: dict,
    event_fingerprint: str,
    tenant_id: uuid.UUID,
) -> bool:
    """Insert raw event — ON CONFLICT DO NOTHING (idempotent)."""
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from attendance.models import DeviceAttendanceEvent

    stmt = pg_insert(DeviceAttendanceEvent).values(
        device_id=device_id,
        device_user_id=device_user_id,
        event_time=event_time,
        verify_type=verify_type,
        verify_state=verify_state,
        work_code=work_code,
        raw_payload=raw_payload,
        event_fingerprint=event_fingerprint,
        tenant_id=tenant_id,
    ).on_conflict_do_nothing(
        index_elements=["device_id", "event_fingerprint"]
    )
    result = await db.execute(stmt)
    return result.rowcount > 0


async def handle_get_request(
    db: AsyncSession,
    serial_number: str,
) -> str:
    """
    Handle GET /iclock/getrequest — device polls for pending commands.
    Returns command string in ADMS format.
    """
    device = await get_device_by_serial(db, serial_number)
    if not device:
        return "OK"

    await update_device_heartbeat(db, device)

    commands = await get_pending_commands(db, device.id)
    if not commands:
        return "OK"

    # Take first pending command
    cmd = commands[0]
    cmd.status = "sent"
    cmd.attempts += 1
    db.add(cmd)
    await db.commit()

    return _format_command(cmd)


def _format_command(cmd) -> str:
    """Format a DeviceCommand into ADMS command string."""
    p = cmd.payload or {}
    cmd_id = str(cmd.id)[:8]

    if cmd.command_type == "CREATE_USER":
        return (
            f"C:{cmd_id}:DATA UPDATE USERINFO "
            f"PIN={p.get('pin', '')} "
            f"Name={p.get('name', '')} "
            f"Pri={p.get('privilege', 0)} "
            f"Passwd={p.get('password', '')} "
            f"Card={p.get('card', '')} "
            f"Grp={p.get('group', 1)} "
            f"TZ={p.get('tz', '0000000100110000')} "
            f"Verify={p.get('verify', 0)}"
        )
    elif cmd.command_type == "DELETE_USER":
        return f"C:{cmd_id}:DATA DELETE USERINFO PIN={p.get('pin', '')}"
    elif cmd.command_type == "REBOOT":
        return f"C:{cmd_id}:REBOOT"
    elif cmd.command_type == "SET_TIME":
        return f"C:{cmd_id}:DATE {p.get('datetime', '')}"
    else:
        return f"C:{cmd_id}:OK"


async def handle_device_cmd(
    db: AsyncSession,
    serial_number: str,
    body: str,
) -> str:
    """
    Handle POST /iclock/devicecmd — device acknowledges command execution.
    Body format: ID=<cmd_id>&Return=<0|error>&CMD=<command_type>
    """
    params = parse_qs(body)
    cmd_id_raw = params.get("ID", [None])[0]
    return_code = params.get("Return", ["0"])[0]

    if cmd_id_raw:
        # Find command by short ID prefix
        from sqlalchemy import select
        from devices.models import DeviceCommand
        result = await db.execute(
            select(DeviceCommand).where(
                DeviceCommand.device_id == (
                    await get_device_by_serial(db, serial_number)
                ).id
            ).where(DeviceCommand.status == "sent")
            .order_by(DeviceCommand.created_at.asc())
            .limit(1)
        )
        cmd = result.scalar_one_or_none()
        if cmd:
            success = return_code == "0"
            await acknowledge_command(db, cmd.id, success=success)
            await db.commit()

    return "OK"


async def handle_ping(db: AsyncSession, serial_number: str) -> str:
    """Handle GET /iclock/ping — heartbeat."""
    device = await get_device_by_serial(db, serial_number)
    if device:
        await update_device_heartbeat(db, device)
        await db.commit()
    return "OK"
