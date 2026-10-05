"""
Employee domain models.
"""
import uuid
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, BYTEA, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import TenantModel


class EmployeeStatus(str, PyEnum):
    ACTIVE     = "active"
    INACTIVE   = "inactive"
    TERMINATED = "terminated"


class BiometricType(str, PyEnum):
    FACE        = "face"
    FINGERPRINT = "fingerprint"
    PALM        = "palm"
    CARD        = "card"
    QR          = "qr"
    PASSWORD    = "password"


class Area(TenantModel):
    __tablename__ = "areas"
    name:     Mapped[str] = mapped_column(String(120), nullable=False)
    timezone: Mapped[str] = mapped_column(String(60), default="UTC")

    departments: Mapped[list["Department"]] = relationship(back_populates="area")
    employees:   Mapped[list["Employee"]]   = relationship(back_populates="area")


class Department(TenantModel):
    __tablename__ = "departments"
    name:      Mapped[str]            = mapped_column(String(120), nullable=False)
    parent_id: Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    area_id:   Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), ForeignKey("areas.id"), nullable=True)

    area:        Mapped["Area|None"]         = relationship(back_populates="departments")
    employees:   Mapped[list["Employee"]]    = relationship(back_populates="department")
    positions:   Mapped[list["Position"]]    = relationship(back_populates="department")


class Position(TenantModel):
    __tablename__ = "positions"
    title:         Mapped[str]            = mapped_column(String(120), nullable=False)
    department_id: Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)

    department: Mapped["Department|None"] = relationship(back_populates="positions")
    employees:  Mapped[list["Employee"]]  = relationship(back_populates="position")


class Employee(TenantModel):
    __tablename__ = "employees"

    employee_code: Mapped[str]            = mapped_column(String(40),  nullable=False, index=True)
    first_name:    Mapped[str]            = mapped_column(String(80),  nullable=False)
    last_name:     Mapped[str]            = mapped_column(String(80),  nullable=False)
    email:         Mapped[str|None]       = mapped_column(String(255), nullable=True)
    phone:         Mapped[str|None]       = mapped_column(String(40),  nullable=True)
    status:        Mapped[str]            = mapped_column(String(20),  default=EmployeeStatus.ACTIVE)
    hire_date:     Mapped[Date|None]      = mapped_column(Date,        nullable=True)
    photo_url:     Mapped[str|None]       = mapped_column(String(500), nullable=True)

    department_id: Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    position_id:   Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), ForeignKey("positions.id"),   nullable=True)
    area_id:       Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), ForeignKey("areas.id"),       nullable=True)

    # ID used on the physical device (PIN)
    device_user_id: Mapped[str|None] = mapped_column(String(20), nullable=True, index=True)

    department: Mapped["Department|None"] = relationship(back_populates="employees")
    position:   Mapped["Position|None"]   = relationship(back_populates="employees")
    area:       Mapped["Area|None"]        = relationship(back_populates="employees")
    biometrics: Mapped[list["EmployeeBiometric"]] = relationship(back_populates="employee", cascade="all, delete-orphan")


class EmployeeBiometric(TenantModel):
    __tablename__ = "employee_biometrics"

    employee_id:    Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    template_type:  Mapped[str]       = mapped_column(String(20), nullable=False)   # face/fingerprint/palm/card/qr
    template_data:  Mapped[bytes|None]= mapped_column(BYTEA, nullable=True)          # encrypted at rest
    device_id:      Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    finger_index:   Mapped[int|None]  = mapped_column(nullable=True)                # 0-9 for fingerprint slots

    employee: Mapped["Employee"] = relationship(back_populates="biometrics")
