"""
WebSocket endpoints.
  /ws/live    — real-time punch feed (auth via token query param)
  /ws/devices — device status updates
"""
import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from core.security import decode_token
from websocket.manager import manager

router = APIRouter()


async def _authenticate_ws(token: str | None) -> dict | None:
    """Decode JWT from query param for WebSocket auth."""
    if not token:
        return None
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None
    return payload


@router.websocket("/live")
async def ws_live_punches(
    websocket: WebSocket,
    token: str | None = Query(default=None),
):
    """
    Real-time live punch feed.
    Connect with: ws://server/ws/live?token=<access_token>
    
    Messages received:
      { "type": "punch", "employee_name": "...", "event_time": "...", ... }
      { "type": "device_status", "serial": "...", "status": "online" }
      { "type": "ping" }
    """
    payload = await _authenticate_ws(token)
    if not payload:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    tenant_id = payload.get("tenant_id", "default")
    await manager.connect(websocket, tenant_id)

    try:
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "BioTime Open live feed connected",
            "tenant_id": tenant_id,
        }))

        # Keep alive — handle incoming messages (ping/pong)
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data) if data else {}
            if msg.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        manager.disconnect(websocket, tenant_id)


@router.websocket("/devices")
async def ws_device_status(
    websocket: WebSocket,
    token: str | None = Query(default=None),
):
    """Device status WebSocket — online/offline/sync updates."""
    payload = await _authenticate_ws(token)
    if not payload:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    tenant_id = payload.get("tenant_id", "default")
    await manager.connect(websocket, f"devices:{tenant_id}")

    try:
        await websocket.send_text(json.dumps({
            "type": "connected",
            "channel": "device_status",
        }))
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, f"devices:{tenant_id}")
