"""Visitor management models."""
import uuid
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from core.models import TenantModel


class Visitor(TenantModel):
    __tablename__ = "visitors"
    name:            Mapped[str]            = mapped_column(String(120), nullable=False)
    company:         Mapped[str|None]       = mapped_column(String(120), nullable=True)
    phone:           Mapped[str|None]       = mapped_column(String(40),  nullable=True)
    id_number:       Mapped[str|None]       = mapped_column(String(80),  nullable=True)
    photo_url:       Mapped[str|None]       = mapped_column(String(500), nullable=True)
    host_employee_id:Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    purpose:         Mapped[str|None]       = mapped_column(Text, nullable=True)
    check_in_at:     Mapped[DateTime|None]  = mapped_column(DateTime(timezone=True), nullable=True)
    check_out_at:    Mapped[DateTime|None]  = mapped_column(DateTime(timezone=True), nullable=True)
    badge_number:    Mapped[str|None]       = mapped_column(String(40),  nullable=True)
    status:          Mapped[str]            = mapped_column(String(20),  default="expected")
