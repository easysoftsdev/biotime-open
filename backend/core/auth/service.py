"""
Auth service — user lookup, creation, password verification.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.models import User, UserRole
from core.exceptions import NotFoundError, UnauthorizedError
from core.security import hash_password, verify_password


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    role: str = UserRole.EMPLOYEE,
    tenant_id: uuid.UUID | None = None,
    employee_id: uuid.UUID | None = None,
) -> User:
    user = User(
        email=email,
        password_hash=hash_password(password),
        role=role,
        tenant_id=tenant_id or uuid.uuid4(),
        employee_id=employee_id,
    )
    db.add(user)
    await db.flush()
    return user


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> User:
    user = await get_user_by_email(db, email)
    if not user:
        raise UnauthorizedError("Invalid email or password")
    if not verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")
    if not user.is_active:
        raise UnauthorizedError("Account is disabled")
    return user


async def change_password(
    db: AsyncSession, user: User, current_password: str, new_password: str
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise UnauthorizedError("Current password is incorrect")
    user.password_hash = hash_password(new_password)
    db.add(user)
    await db.flush()
