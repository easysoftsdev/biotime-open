"""
Auth endpoints — login, refresh, me, TOTP setup, change password.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import schemas, service
from core.database import get_db
from core.deps import CurrentUser
from core.exceptions import UnauthorizedError
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_totp_secret,
    get_totp_uri,
    verify_totp,
)

router = APIRouter()


@router.post("/login", response_model=schemas.TokenResponse)
async def login(
    body: schemas.LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await service.authenticate_user(db, body.email, body.password)

    # TOTP check if enabled
    if user.totp_enabled:
        if not body.totp_code:
            raise UnauthorizedError("TOTP code required")
        if not verify_totp(user.totp_secret, body.totp_code):
            raise UnauthorizedError("Invalid TOTP code")

    extra = {"role": user.role, "tenant_id": str(user.tenant_id)}
    return schemas.TokenResponse(
        access_token=create_access_token(user.id, extra=extra),
        refresh_token=create_refresh_token(user.id),
        role=user.role,
        tenant_id=str(user.tenant_id),
    )


@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh(
    body: schemas.RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid refresh token")

    import uuid
    user = await service.get_user_by_id(db, uuid.UUID(payload["sub"]))
    if not user or not user.is_active:
        raise UnauthorizedError("User not found")

    extra = {"role": user.role, "tenant_id": str(user.tenant_id)}
    return schemas.TokenResponse(
        access_token=create_access_token(user.id, extra=extra),
        refresh_token=create_refresh_token(user.id),
        role=user.role,
        tenant_id=str(user.tenant_id),
    )


@router.get("/me", response_model=schemas.UserOut)
async def me(current_user=Depends(CurrentUser)):  # type: ignore[valid-type]
    return current_user


@router.post("/change-password", status_code=204)
async def change_password(
    body: schemas.ChangePasswordRequest,
    current_user=Depends(CurrentUser),  # type: ignore[valid-type]
    db: AsyncSession = Depends(get_db),
):
    await service.change_password(db, current_user, body.current_password, body.new_password)


@router.post("/totp/setup", response_model=schemas.TOTPSetupResponse)
async def totp_setup(current_user=Depends(CurrentUser)):  # type: ignore[valid-type]
    secret = generate_totp_secret()
    uri = get_totp_uri(secret, current_user.email)
    # Secret is not saved yet — user must verify first
    return schemas.TOTPSetupResponse(secret=secret, uri=uri)


@router.post("/totp/verify", status_code=204)
async def totp_verify(
    body: schemas.TOTPVerifyRequest,
    current_user=Depends(CurrentUser),  # type: ignore[valid-type]
    db: AsyncSession = Depends(get_db),
):
    """Verify TOTP code and activate 2FA for the user."""
    if not verify_totp(body.secret if hasattr(body, "secret") else current_user.totp_secret, body.code):
        raise UnauthorizedError("Invalid TOTP code")
    current_user.totp_enabled = True
    db.add(current_user)
