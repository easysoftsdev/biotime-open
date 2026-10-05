"""HRM Push Layer models."""
import uuid
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.models import TenantModel


class HRMPushTarget(TenantModel):
    """A configured HRM/ERP system to push attendance data to."""
    __tablename__ = "hrm_push_targets"

    name:                Mapped[str]  = mapped_column(String(120), nullable=False)
    type:                Mapped[str]  = mapped_column(String(40),  default="custom")  # odoo/sap/zoho/bamboohr/custom
    base_url:            Mapped[str]  = mapped_column(String(500), nullable=False)
    auth_config:         Mapped[dict] = mapped_column(JSONB, default=dict)  # {type, token/user/pass/key}
    field_map:           Mapped[dict] = mapped_column(JSONB, default=dict)  # {our_field: target_field}
    event_subscriptions: Mapped[list] = mapped_column(JSONB, default=list)  # ["punch_in","punch_out",...]
    headers:             Mapped[dict] = mapped_column(JSONB, default=dict)  # extra HTTP headers
    active:              Mapped[bool] = mapped_column(Boolean, default=True)
    retry_max_attempts:  Mapped[int]  = mapped_column(Integer, default=5)
    timeout_seconds:     Mapped[int]  = mapped_column(Integer, default=30)
    verify_ssl:          Mapped[bool] = mapped_column(Boolean, default=True)

    jobs: Mapped[list["HRMPushJob"]] = relationship(back_populates="target", cascade="all, delete-orphan")


class HRMPushJob(TenantModel):
    """A single push attempt to an HRM target."""
    __tablename__ = "hrm_push_jobs"

    target_id:    Mapped[uuid.UUID]      = mapped_column(UUID(as_uuid=True), ForeignKey("hrm_push_targets.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type:   Mapped[str]            = mapped_column(String(40),  nullable=False)
    employee_id:  Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), nullable=True)
    payload:      Mapped[dict]           = mapped_column(JSONB, default=dict)
    status:       Mapped[str]            = mapped_column(String(20), default="queued")  # queued/sent/failed/retrying
    attempts:     Mapped[int]            = mapped_column(Integer, default=0)
    next_retry_at:Mapped[DateTime|None]  = mapped_column(DateTime(timezone=True), nullable=True)
    error:        Mapped[str|None]       = mapped_column(Text, nullable=True)

    target: Mapped["HRMPushTarget"] = relationship(back_populates="jobs")
    logs:   Mapped[list["PushLog"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class PushLog(TenantModel):
    """Immutable audit log of every push attempt."""
    __tablename__ = "push_logs"

    target_id:       Mapped[uuid.UUID]      = mapped_column(UUID(as_uuid=True), nullable=False)
    job_id:          Mapped[uuid.UUID]       = mapped_column(UUID(as_uuid=True), ForeignKey("hrm_push_jobs.id", ondelete="CASCADE"), nullable=False)
    event_type:      Mapped[str]             = mapped_column(String(40))
    employee_id:     Mapped[uuid.UUID|None]  = mapped_column(UUID(as_uuid=True), nullable=True)
    payload:         Mapped[dict]            = mapped_column(JSONB, default=dict)
    response_status: Mapped[int|None]        = mapped_column(Integer, nullable=True)
    response_body:   Mapped[str|None]        = mapped_column(Text, nullable=True)
    attempt_number:  Mapped[int]             = mapped_column(Integer, default=1)
    sent_at:         Mapped[DateTime|None]   = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms:     Mapped[int]             = mapped_column(Integer, default=0)
    success:         Mapped[bool]            = mapped_column(Boolean, default=False)

    job: Mapped["HRMPushJob"] = relationship(back_populates="logs")
