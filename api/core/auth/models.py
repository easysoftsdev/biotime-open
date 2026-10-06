"""
User and Tenant database models.
"""
import uuid
from enum import Enum as PyEnum

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import BaseModel, TenantModel


class UserRole(str, PyEnum):
    SUPER_ADMIN = "super_admin"
    HR_ADMIN    = "hr_admin"
    MANAGER     = "manager"
    EMPLOYEE    = "employee"


class Tenant(BaseModel):
    __tablename__ = "tenants"

    name: Mapped[str]     = mapped_column(String(120), nullable=False)
    slug: Mapped[str]     = mapped_column(String(80), unique=True, nullable=False)
    plan: Mapped[str]     = mapped_column(String(40), default="standard")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    users: Mapped[list["User"]] = relationship(back_populates="tenant")


class User(TenantModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str]  = mapped_column(String(255), nullable=False)
    role: Mapped[str]           = mapped_column(String(40), default=UserRole.EMPLOYEE)
    is_active: Mapped[bool]     = mapped_column(Boolean, default=True)
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    totp_enabled: Mapped[bool]  = mapped_column(Boolean, default=False)

    # Link to employee record (optional — super_admin may not have one)
    employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="users")
