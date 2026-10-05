"""
Celery application instance + beat schedule.
"""
from celery import Celery
from celery.schedules import crontab

from core.config import settings

celery_app = Celery(
    "biotime",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "tasks.device_tasks",
        "tasks.attendance_tasks",
        "tasks.hrm_push_tasks",
        "tasks.report_tasks",
        "tasks.leave_tasks",
        "tasks.notification_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# ─── Beat schedule ────────────────────────────────────────────
celery_app.conf.beat_schedule = {
    # Every 1 min — check device heartbeats
    "device-health-check": {
        "task": "tasks.device_tasks.check_device_health",
        "schedule": 60.0,
    },
    # Every 5 min — retry failed sync jobs
    "auto-sync-retry": {
        "task": "tasks.device_tasks.retry_failed_syncs",
        "schedule": 300.0,
    },
    # Every 5 min — retry failed HRM push jobs
    "hrm-push-retry": {
        "task": "tasks.hrm_push_tasks.retry_failed_push_jobs",
        "schedule": 300.0,
    },
    # Nightly 01:00 — recalculate attendance
    "attendance-nightly-recalc": {
        "task": "tasks.attendance_tasks.nightly_recalculate",
        "schedule": crontab(hour=1, minute=0),
    },
    # Daily 00:05 — leave accrual
    "leave-daily-accrual": {
        "task": "tasks.leave_tasks.daily_accrual",
        "schedule": crontab(hour=0, minute=5),
    },
}
