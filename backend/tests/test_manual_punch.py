"""
Manual punch request → approval → raw event injection.
"""
import uuid

import pytest
from httpx import AsyncClient, ASGITransport

from main import app
from core.database import AsyncSessionLocal
from core.auth.models import Tenant
from core.auth.service import create_user
from core.security import create_access_token


async def _auth_headers() -> dict[str, str]:
    """Fresh tenant + super admin, returned as request headers."""
    suffix = uuid.uuid4().hex[:8]
    async with AsyncSessionLocal() as db:
        tenant = Tenant(name=f"Manual Punch {suffix}", slug=f"mp-{suffix}")
        db.add(tenant)
        await db.flush()
        user = await create_user(
            db,
            email=f"mp-{suffix}@test.local",
            password="Passw0rd!test",
            role="super_admin",
            tenant_id=tenant.id,
        )
        await db.commit()
        user_id = str(user.id)
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_manual_punch_approve_flow():
    headers = await _auth_headers()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. employee to punch for
        code = f"MP{uuid.uuid4().hex[:6].upper()}"
        resp = await client.post(
            "/api/v1/employees",
            json={"employee_code": code, "first_name": "Manual", "last_name": "Tester"},
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        employee_id = resp.json()["id"]

        # 2. submit the request — stays pending
        resp = await client.post(
            "/api/v1/attendance/manual-punch",
            json={
                "employee_id": employee_id,
                "requested_time": "2026-10-05T09:15:00Z",
                "punch_type": "in",
                "reason": "Forgot to badge in",
            },
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        request_id = resp.json()["id"]
        assert resp.json()["status"] == "pending"

        # 3. it shows up in the pending queue
        resp = await client.get(
            "/api/v1/attendance/manual-punch?status=pending", headers=headers
        )
        assert resp.status_code == 200, resp.text
        assert request_id in [r["id"] for r in resp.json()]

        # 4. approve → approved + raw event injected
        resp = await client.put(
            f"/api/v1/attendance/manual-punch/{request_id}/approve",
            params={"approve": "true"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "approved"
        assert resp.json()["approved_at"] is not None

        resp = await client.get(
            "/api/v1/attendance/manual-punch?status=approved", headers=headers
        )
        assert request_id in [r["id"] for r in resp.json()]

        # approving twice is rejected
        resp = await client.put(
            f"/api/v1/attendance/manual-punch/{request_id}/approve",
            params={"approve": "true"},
            headers=headers,
        )
        assert resp.status_code == 409, resp.text

        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            from attendance.models import (
                AttendanceRecord, DeviceAttendanceEvent,
                MANUAL_PUNCH_DEVICE_USER_ID,
            )
            from attendance.engine import process_employee_events

            events = (
                (
                    await db.execute(
                        select(DeviceAttendanceEvent).where(
                            DeviceAttendanceEvent.employee_id
                            == uuid.UUID(employee_id),
                        )
                    )
                )
                .scalars()
                .all()
            )
        assert len(events) == 1, "approval should inject exactly one raw event"
        assert events[0].device_user_id == MANUAL_PUNCH_DEVICE_USER_ID
        assert events[0].device_id is None

        # processing the injected event must flag the record as manual
        async with AsyncSessionLocal() as db:
            updated = await process_employee_events(
                db, uuid.UUID(employee_id)
            )
            await db.commit()
        assert updated == 1

        async with AsyncSessionLocal() as db:
            record = (
                await db.execute(
                    select(AttendanceRecord).where(
                        AttendanceRecord.employee_id == uuid.UUID(employee_id)
                    )
                )
            ).scalar_one()
        assert record.is_manual is True
        assert record.first_in is not None


@pytest.mark.asyncio
async def test_manual_punch_reject_keeps_records_untouched():
    headers = await _auth_headers()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        code = f"MP{uuid.uuid4().hex[:6].upper()}"
        resp = await client.post(
            "/api/v1/employees",
            json={"employee_code": code, "first_name": "Reject", "last_name": "Tester"},
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        employee_id = resp.json()["id"]

        resp = await client.post(
            "/api/v1/attendance/manual-punch",
            json={
                "employee_id": employee_id,
                "requested_time": "2026-10-05T18:40:00Z",
                "punch_type": "out",
            },
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        request_id = resp.json()["id"]

        resp = await client.put(
            f"/api/v1/attendance/manual-punch/{request_id}/approve",
            params={"approve": "false", "reject_reason": "No manager approval"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "rejected"
        assert resp.json()["rejected_reason"] == "No manager approval"

        async with AsyncSessionLocal() as db:
            from sqlalchemy import select, func
            from attendance.models import DeviceAttendanceEvent

            count = (
                await db.execute(
                    select(func.count())
                    .select_from(DeviceAttendanceEvent)
                    .where(
                        DeviceAttendanceEvent.device_user_id == "manual",
                        DeviceAttendanceEvent.employee_id
                        == uuid.UUID(employee_id),
                    )
                )
            ).scalar_one()
        assert count == 0, "rejected request must not inject a punch"
