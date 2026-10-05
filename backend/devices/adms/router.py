"""
ADMS endpoints — ZKTeco device communication.
All devices point their server URL to /iclock/
"""
import uuid

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from devices.adms.handler import (
    handle_attendance_upload,
    handle_device_cmd,
    handle_get_request,
    handle_handshake,
    handle_ping,
)

router = APIRouter()

# ─── Default tenant for ADMS (devices don't send tenant info) ─
# In production, resolve tenant from IP range or device serial prefix.
DEFAULT_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _get_tenant_id(request: Request) -> uuid.UUID:
    """
    Resolve tenant from request.
    For now uses a default; extend to map by IP or serial prefix.
    """
    return DEFAULT_TENANT_ID


@router.get("/cdata", response_class=PlainTextResponse)
async def adms_handshake(
    request: Request,
    SN: str = Query(..., description="Device serial number"),
    options: str = Query(default="", description="Device options string"),
    db: AsyncSession = Depends(get_db),
):
    """
    Device handshake — called when device starts up or reconnects.
    Parses serial, firmware, model from query params.
    """
    params = dict(request.query_params)
    firmware = params.get("Pushver") or params.get("FWVersion") or params.get("Ver")
    model    = params.get("DeviceModel") or params.get("Model")
    language = params.get("Language")
    tenant_id = _get_tenant_id(request)

    response = await handle_handshake(db, SN, firmware, model, language, tenant_id)
    return PlainTextResponse(content=response)


@router.post("/cdata", response_class=PlainTextResponse)
async def adms_upload(
    request: Request,
    SN: str = Query(..., description="Device serial number"),
    table: str = Query(default="ATTLOG", description="Data table type"),
    db: AsyncSession = Depends(get_db),
):
    """
    Device uploads attendance records.
    Body contains tab-separated ATTLOG lines.
    """
    body = await request.body()
    raw = body.decode("utf-8", errors="replace")
    tenant_id = _get_tenant_id(request)

    result = await handle_attendance_upload(db, SN, raw, tenant_id)
    return PlainTextResponse(content=f"OK: {result['inserted']} new records")


@router.get("/getrequest", response_class=PlainTextResponse)
async def adms_get_request(
    request: Request,
    SN: str = Query(..., description="Device serial number"),
    db: AsyncSession = Depends(get_db),
):
    """Device polls for pending commands every 30–60 seconds."""
    response = await handle_get_request(db, SN)
    return PlainTextResponse(content=response)


@router.post("/devicecmd", response_class=PlainTextResponse)
async def adms_device_cmd(
    request: Request,
    SN: str = Query(..., description="Device serial number"),
    db: AsyncSession = Depends(get_db),
):
    """Device confirms command execution result."""
    body = await request.body()
    raw = body.decode("utf-8", errors="replace")
    response = await handle_device_cmd(db, SN, raw)
    return PlainTextResponse(content=response)


@router.get("/ping", response_class=PlainTextResponse)
async def adms_ping(
    request: Request,
    SN: str = Query(..., description="Device serial number"),
    db: AsyncSession = Depends(get_db),
):
    """Device heartbeat — sent every 30–60 seconds."""
    response = await handle_ping(db, SN)
    return PlainTextResponse(content=response)
