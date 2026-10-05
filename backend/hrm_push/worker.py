"""
HRM Push Worker — executes a single push job.

Handles auth types: bearer, basic, api_key, oauth2
Applies field_map to transform attendance payload to target HRM format.
Logs every attempt to push_logs.
"""
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx

from core.database import AsyncSessionLocal


BACKOFF_SECONDS = [60, 300, 900, 3600, 7200]  # 1m, 5m, 15m, 1h, 2h


async def execute_push_job(job_id: uuid.UUID) -> bool:
    """Execute a single HRM push job. Returns True on success."""
    async with AsyncSessionLocal() as db:
        from hrm_push.models import HRMPushJob, HRMPushTarget, PushLog
        from sqlalchemy import select

        result = await db.execute(
            select(HRMPushJob).where(HRMPushJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            return False

        target_result = await db.execute(
            select(HRMPushTarget).where(HRMPushTarget.id == job.target_id)
        )
        target = target_result.scalar_one_or_none()
        if not target or not target.active:
            job.status = "failed"
            job.error = "Target not found or inactive"
            db.add(job)
            await db.commit()
            return False

        # Apply field map
        payload = _apply_field_map(job.payload, target.field_map)

        # Build auth headers
        headers = dict(target.headers or {})
        headers.update(_build_auth_headers(target.auth_config))
        headers["Content-Type"] = "application/json"

        # Execute HTTP call
        start = time.perf_counter()
        success = False
        response_status = None
        response_body = None
        error = None

        try:
            async with httpx.AsyncClient(
                verify=target.verify_ssl,
                timeout=target.timeout_seconds,
            ) as client:
                resp = await client.post(target.base_url, json=payload, headers=headers)
                response_status = resp.status_code
                response_body = resp.text[:2000]
                success = resp.is_success
        except httpx.TimeoutException:
            error = "Request timed out"
        except httpx.RequestError as e:
            error = f"Request error: {str(e)[:200]}"

        duration_ms = int((time.perf_counter() - start) * 1000)

        # Log the attempt
        log = PushLog(
            tenant_id=job.tenant_id,
            target_id=target.id,
            job_id=job.id,
            event_type=job.event_type,
            employee_id=job.employee_id,
            payload=payload,
            response_status=response_status,
            response_body=response_body,
            attempt_number=job.attempts + 1,
            sent_at=datetime.now(timezone.utc),
            duration_ms=duration_ms,
            success=success,
        )
        db.add(log)

        # Update job
        job.attempts += 1
        if success:
            job.status = "sent"
            job.error = None
        else:
            job.error = error or f"HTTP {response_status}"
            if job.attempts >= target.retry_max_attempts:
                job.status = "failed"
            else:
                job.status = "retrying"
                delay = BACKOFF_SECONDS[min(job.attempts - 1, len(BACKOFF_SECONDS) - 1)]
                job.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
        db.add(job)
        await db.commit()
        return success


def _apply_field_map(payload: dict, field_map: dict) -> dict:
    """
    Transform payload using field_map.
    field_map: {"our_field": "target_field"}
    Supports dot-notation for nested target fields: "check_in" -> "attendance.check_in"
    """
    if not field_map:
        return payload

    result: dict[str, Any] = {}
    for src_key, dst_key in field_map.items():
        if src_key in payload:
            _set_nested(result, dst_key, payload[src_key])

    # Include unmapped fields
    mapped_keys = set(field_map.keys())
    for k, v in payload.items():
        if k not in mapped_keys:
            result[k] = v

    return result


def _set_nested(obj: dict, path: str, value) -> None:
    """Set a value in a nested dict using dot-notation path."""
    parts = path.split(".")
    for part in parts[:-1]:
        obj = obj.setdefault(part, {})
    obj[parts[-1]] = value


def _build_auth_headers(auth_config: dict) -> dict:
    """Build HTTP auth headers from auth config."""
    if not auth_config:
        return {}

    auth_type = auth_config.get("type", "")

    if auth_type == "bearer":
        return {"Authorization": f"Bearer {auth_config.get('token', '')}"}

    elif auth_type == "basic":
        import base64
        creds = f"{auth_config.get('user', '')}:{auth_config.get('password', '')}"
        encoded = base64.b64encode(creds.encode()).decode()
        return {"Authorization": f"Basic {encoded}"}

    elif auth_type == "api_key":
        header_name = auth_config.get("header", "X-API-Key")
        return {header_name: auth_config.get("key", "")}

    return {}
