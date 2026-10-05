"""
Async SQLAlchemy database engine, session factory, and base model.
"""
from typing import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from core.config import settings

# ─── Engine ───────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# ─── Session factory ──────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# ─── Naming convention for Alembic migrations ─────────────────
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# ─── Declarative base ─────────────────────────────────────────
class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)


# ─── Dependency ───────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ─── Create tables (used in lifespan) ─────────────────────────
async def create_tables():
    # Import all models so Base.metadata knows about them
    import devices.models       # noqa: F401
    import employees.models     # noqa: F401
    import attendance.models    # noqa: F401
    import shifts.models        # noqa: F401
    import leave.models         # noqa: F401
    import payroll.models       # noqa: F401
    import hrm_push.models      # noqa: F401
    import access.models        # noqa: F401
    import visitors.models      # noqa: F401
    import sync.models          # noqa: F401
    import core.auth.models     # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
