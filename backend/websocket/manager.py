"""
WebSocket connection manager.
Broadcasts real-time punch events to all connected dashboard clients.
"""
import json
import uuid
from typing import dict as Dict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # tenant_id -> list of active WebSocket connections
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, tenant_id: str):
        await websocket.accept()
        self._connections.setdefault(tenant_id, []).append(websocket)

    def disconnect(self, websocket: WebSocket, tenant_id: str):
        connections = self._connections.get(tenant_id, [])
        if websocket in connections:
            connections.remove(websocket)

    async def broadcast(self, tenant_id: str, message: dict):
        """Send a message to all connections for a tenant."""
        connections = self._connections.get(tenant_id, [])
        dead = []
        for ws in connections:
            try:
                await ws.send_text(json.dumps(message, default=str))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, tenant_id)

    async def broadcast_all(self, message: dict):
        """Send to all connected clients across all tenants."""
        for tenant_id in list(self._connections.keys()):
            await self.broadcast(tenant_id, message)

    def active_count(self, tenant_id: str) -> int:
        return len(self._connections.get(tenant_id, []))


# Global singleton
manager = ConnectionManager()


async def broadcast_punch(
    tenant_id: str,
    employee_id: str,
    employee_name: str,
    device_serial: str,
    event_time: str,
    verify_type: int,
    status: str,
):
    """Convenience function called by the attendance engine after punch ingestion."""
    await manager.broadcast(tenant_id, {
        "type": "punch",
        "employee_id": employee_id,
        "employee_name": employee_name,
        "device_serial": device_serial,
        "event_time": event_time,
        "verify_type": verify_type,
        "status": status,
    })


async def broadcast_device_status(tenant_id: str, device_id: str, serial: str, status: str):
    """Broadcast device online/offline status change."""
    await manager.broadcast(tenant_id, {
        "type": "device_status",
        "device_id": device_id,
        "serial": serial,
        "status": status,
    })
