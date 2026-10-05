"""
FastAPI dependency injection — current user, tenant, DB session.
"""
import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.models import User
from core.database import get_db
from core.exceptions import UnauthorizedError, ForbiddenError
from core.security import decode_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
):
    """Decode JWT and return the authenticated user."""
    from core.auth.service import get_user_by_id

    if not credentials:
        raise UnauthorizedError("Missing authorization token")

    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedError("Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")

    user = await get_user_by_id(db, uuid.UUID(user_id))
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    return user


async def require_roles(*roles: str):
    """Factory: returns a dependency that enforces role membership."""
    async def _check(
        current_user=Depends(get_current_user),
    ):
        if current_user.role not in roles:
            raise ForbiddenError(
                f"Role '{current_user.role}' is not permitted for this action"
            )
        return current_user
    return _check


# ─── Typed shortcuts ──────────────────────────────────────────
CurrentUser = Annotated[User, Depends(get_current_user)]
DBSession = Annotated[AsyncSession, Depends(get_db)]
