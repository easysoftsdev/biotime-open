"""Access control models."""
import uuid
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from core.models import TenantModel


class AccessGroup(TenantModel):
    __tablename__ = "access_groups"
    name:      Mapped[str]            = mapped_column(String(120), nullable=False)
    device_id: Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    door_id:   Mapped[str|None]       = mapped_column(String(20), nullable=True)
    schedule:  Mapped[dict]           = mapped_column(JSONB, default=dict)


class EmployeeAccess(TenantModel):
    __tablename__ = "employee_access"
    employee_id:     Mapped[uuid.UUID]      = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    access_group_id: Mapped[uuid.UUID]      = mapped_column(UUID(as_uuid=True), ForeignKey("access_groups.id", ondelete="CASCADE"), nullable=False)
    valid_from:      Mapped[Date|None]      = mapped_column(Date, nullable=True)
    valid_to:        Mapped[Date|None]      = mapped_column(Date, nullable=True)
