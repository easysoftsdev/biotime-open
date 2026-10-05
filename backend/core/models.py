"""
Shared base model mixins used across all domain models.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UUIDMixin:
    """Primary key as UUID."""
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """Created/updated timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TenantMixin:
    """Tenant isolation — every domain table carries tenant_id."""
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )


class BaseModel(UUIDMixin, TimestampMixin, Base):
    """Abstract base — UUID pk + timestamps. No tenant."""
    __abstract__ = True


class TenantModel(UUIDMixin, TimestampMixin, TenantMixin, Base):
    """Abstract base — UUID pk + timestamps + tenant_id."""
    __abstract__ = True
