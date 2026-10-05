"""
Auth request / response schemas.
"""
import uuid

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    tenant_id: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    tenant_id: uuid.UUID
    is_active: bool
    totp_enabled: bool

    model_config = {"from_attributes": True}


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class TOTPSetupResponse(BaseModel):
    secret: str
    uri: str


class TOTPVerifyRequest(BaseModel):
    code: str
    secret: str | None = None
