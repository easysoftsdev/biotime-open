"""
Basic ADMS endpoint tests.
"""
import pytest

from httpx import AsyncClient, ASGITransport

from main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_adms_ping_unknown_device():
    """Unknown device ping should still return OK."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/iclock/ping?SN=TEST000001")
    assert resp.status_code == 200
    assert "OK" in resp.text


@pytest.mark.asyncio
async def test_adms_handshake():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/iclock/cdata?SN=TEST000001&options=all&pushver=2.4.1")
    assert resp.status_code == 200
    assert "GET OPTION FROM" in resp.text


@pytest.mark.asyncio
async def test_adms_handshake_sets_online_status():
    from core.database import AsyncSessionLocal
    from devices.service import get_device_by_serial
    from devices.models import DeviceStatus

    sn = "TEST_STATUS_001"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/iclock/cdata?SN={sn}&options=all&pushver=2.4.1")
    assert resp.status_code == 200

    async with AsyncSessionLocal() as db:
        dev = await get_device_by_serial(db, sn)
        assert dev is not None
        assert dev.status == DeviceStatus.ONLINE
