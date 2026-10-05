"""
BioTime Open — Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from core.config import settings
from core.database import create_tables
from core.middleware import RequestLoggingMiddleware

# ─── Routers ──────────────────────────────────────────────────
from devices.router import router as devices_router
from devices.adms.router import router as adms_router
from employees.router import router as employees_router
from attendance.router import router as attendance_router
from shifts.router import router as shifts_router
from leave.router import router as leave_router
from payroll.router import router as payroll_router
from hrm_push.router import router as hrm_push_router
from access.router import router as access_router
from visitors.router import router as visitors_router
from reports.router import router as reports_router
from sync.router import router as sync_router
from websocket.router import router as ws_router
from core.auth.router import router as auth_router


# ─── Sentry ───────────────────────────────────────────────────
if settings.SENTRY_DSN:
    sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)


# ─── Lifespan ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_tables()
    yield
    # Shutdown — nothing to clean up


# ─── App factory ──────────────────────────────────────────────
app = FastAPI(
    title="BioTime Open",
    description="Open-source ZKTeco attendance platform. Connect any device, push to any HRM.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ─── Middleware ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RequestLoggingMiddleware)

# ─── Prometheus metrics ───────────────────────────────────────
Instrumentator().instrument(app).expose(app)

# ─── Routes ───────────────────────────────────────────────────
app.include_router(auth_router,       prefix="/api/v1/auth",       tags=["Auth"])
app.include_router(devices_router,    prefix="/api/v1/devices",    tags=["Devices"])
app.include_router(adms_router,       prefix="/iclock",            tags=["ADMS"])
app.include_router(employees_router,  prefix="/api/v1/employees",  tags=["Employees"])
app.include_router(attendance_router, prefix="/api/v1/attendance", tags=["Attendance"])
app.include_router(shifts_router,     prefix="/api/v1/shifts",     tags=["Shifts"])
app.include_router(leave_router,      prefix="/api/v1/leave",      tags=["Leave"])
app.include_router(payroll_router,    prefix="/api/v1/payroll",    tags=["Payroll"])
app.include_router(hrm_push_router,   prefix="/api/v1/hrm",        tags=["HRM Push"])
app.include_router(access_router,     prefix="/api/v1/access",     tags=["Access Control"])
app.include_router(visitors_router,   prefix="/api/v1/visitors",   tags=["Visitors"])
app.include_router(reports_router,    prefix="/api/v1/reports",    tags=["Reports"])
app.include_router(sync_router,       prefix="/api/v1/sync-jobs",  tags=["Sync Jobs"])
app.include_router(ws_router,         prefix="/ws",                tags=["WebSocket"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
