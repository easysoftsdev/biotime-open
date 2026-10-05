"""
Seed initial data — device models registry + first admin user.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.models import Tenant, User, UserRole
from core.config import settings
from core.security import hash_password


DEVICE_MODELS = [
    # SpeedFace V5L Series
    {"series": "SpeedFace-V5L", "model_code": "V5L",         "display_name": "SpeedFace-V5L",         "adms": True, "push_sdk": True,  "tcp": False},
    {"series": "SpeedFace-V5L", "model_code": "V5L[QR]",     "display_name": "SpeedFace-V5L[QR]",     "adms": True, "push_sdk": True,  "tcp": False},
    {"series": "SpeedFace-V5L", "model_code": "V5L[TD]",     "display_name": "SpeedFace-V5L[TD]",     "adms": True, "push_sdk": True,  "tcp": False},
    {"series": "SpeedFace-V5L", "model_code": "V5L[TI]",     "display_name": "SpeedFace-V5L[TI]",     "adms": True, "push_sdk": True,  "tcp": False},
    {"series": "SpeedFace-V5L", "model_code": "V5L[QR][TI]", "display_name": "SpeedFace-V5L[QR][TI]", "adms": True, "push_sdk": True,  "tcp": False},
    # SpeedFace V4L Pro
    {"series": "SpeedFace-V4L", "model_code": "V4L Pro",      "display_name": "SpeedFace-V4L Pro",     "adms": True, "push_sdk": True,  "tcp": False},
    {"series": "SpeedFace-V4L", "model_code": "V4L Pro-QR",   "display_name": "SpeedFace-V4L Pro-QR",  "adms": True, "push_sdk": True,  "tcp": False},
    {"series": "SpeedFace-V4L", "model_code": "V4L Pro-RFID", "display_name": "SpeedFace-V4L Pro-RFID","adms": True, "push_sdk": True,  "tcp": False},
    # SpeedFace V3L
    {"series": "SpeedFace-V3L", "model_code": "V3L",          "display_name": "SpeedFace-V3L",         "adms": True, "push_sdk": False, "tcp": False},
    {"series": "SpeedFace-V3L", "model_code": "V3L[QR]",      "display_name": "SpeedFace-V3L[QR]",     "adms": True, "push_sdk": False, "tcp": False},
    {"series": "SpeedFace-V3L", "model_code": "V3L[RFID]",    "display_name": "SpeedFace-V3L[RFID]",   "adms": True, "push_sdk": False, "tcp": False},
    {"series": "SpeedFace-V3L", "model_code": "V3L Lite",     "display_name": "SpeedFace-V3L Lite",    "adms": True, "push_sdk": False, "tcp": False},
    # SpeedFace H5L
    {"series": "SpeedFace-H5L", "model_code": "H5L",          "display_name": "SpeedFace-H5L",         "adms": True, "push_sdk": True,  "tcp": False},
    {"series": "SpeedFace-H5L", "model_code": "H5L[P]",       "display_name": "SpeedFace-H5L[P]",      "adms": True, "push_sdk": True,  "tcp": False},
    # SenseFace
    {"series": "SenseFace-7",   "model_code": "SenseFace 7",    "display_name": "SenseFace 7",          "adms": True, "push_sdk": True,  "tcp": False},
    {"series": "SenseFace-7",   "model_code": "SenseFace 7[TD]","display_name": "SenseFace 7[TD]",      "adms": True, "push_sdk": True,  "tcp": False},
    {"series": "SenseFace-8",   "model_code": "SenseFace 8",    "display_name": "SenseFace 8",          "adms": True, "push_sdk": True,  "tcp": False},
    # M Series
    {"series": "SpeedFace-M",   "model_code": "M4",            "display_name": "SpeedFace-M4",          "adms": True, "push_sdk": False, "tcp": False},
    {"series": "SpeedFace-M",   "model_code": "M1",            "display_name": "SpeedFace-M1",          "adms": True, "push_sdk": False, "tcp": False},
    {"series": "SpeedFace-M",   "model_code": "M2",            "display_name": "SpeedFace-M2",          "adms": True, "push_sdk": False, "tcp": False},
    # K Series
    {"series": "K-Series",      "model_code": "K40",           "display_name": "K40",                   "adms": True, "push_sdk": False, "tcp": False},
    {"series": "K-Series",      "model_code": "K40 Pro",       "display_name": "K40 Pro",               "adms": True, "push_sdk": False, "tcp": False},
    {"series": "K-Series",      "model_code": "K50",           "display_name": "K50",                   "adms": True, "push_sdk": False, "tcp": False},
    {"series": "K-Series",      "model_code": "K60",           "display_name": "K60",                   "adms": True, "push_sdk": False, "tcp": False},
    # F Series
    {"series": "F-Series",      "model_code": "F18",           "display_name": "F18",                   "adms": True, "push_sdk": False, "tcp": False},
    {"series": "F-Series",      "model_code": "F21",           "display_name": "F21",                   "adms": True, "push_sdk": False, "tcp": False},
    {"series": "F-Series",      "model_code": "F22",           "display_name": "F22",                   "adms": True, "push_sdk": False, "tcp": False},
    {"series": "F-Series",      "model_code": "F35",           "display_name": "F35",                   "adms": True, "push_sdk": False, "tcp": False},
    # Legacy TCP
    {"series": "Legacy",        "model_code": "V5",            "display_name": "SpeedFace V5 (Legacy)", "adms": False,"push_sdk": False, "tcp": True},
    # Generic fallback
    {"series": "Generic",       "model_code": "GENERIC_ADMS",  "display_name": "Generic ADMS Device",  "adms": True, "push_sdk": False, "tcp": False},
]


async def run_seed(db: AsyncSession) -> None:
    await _seed_tenant_and_admin(db)
    await _seed_device_models(db)
    await db.commit()
    print("Seed complete.")


async def _seed_tenant_and_admin(db: AsyncSession) -> None:
    from core.auth.models import Tenant, User

    # Create default tenant
    result = await db.execute(select(Tenant).where(Tenant.slug == "default"))
    tenant = result.scalar_one_or_none()
    if not tenant:
        tenant = Tenant(id=uuid.uuid4(), name="Default Organization", slug="default")
        db.add(tenant)
        await db.flush()
        print(f"  Created tenant: {tenant.name}")

    # Create first admin user
    result = await db.execute(
        select(User).where(User.email == settings.FIRST_ADMIN_EMAIL)
    )
    if not result.scalar_one_or_none():
        user = User(
            email=settings.FIRST_ADMIN_EMAIL,
            password_hash=hash_password(settings.FIRST_ADMIN_PASSWORD),
            role=UserRole.SUPER_ADMIN,
            tenant_id=tenant.id,
        )
        db.add(user)
        print(f"  Created admin: {user.email}")


async def _seed_device_models(db: AsyncSession) -> None:
    from devices.models import DeviceModel

    for m in DEVICE_MODELS:
        result = await db.execute(
            select(DeviceModel).where(DeviceModel.model_code == m["model_code"])
        )
        if not result.scalar_one_or_none():
            db.add(DeviceModel(
                series=m["series"],
                model_code=m["model_code"],
                display_name=m["display_name"],
                adms_supported=m["adms"],
                push_sdk_supported=m["push_sdk"],
                tcp_supported=m["tcp"],
                default_capabilities={
                    "supports_face": True,
                    "supports_fingerprint": not m["push_sdk"],
                    "supports_rfid": "RFID" in m["model_code"],
                    "supports_qr": "QR" in m["model_code"],
                    "supports_temperature": "[TD]" in m["model_code"] or "[TI]" in m["model_code"],
                    "max_users": 50000,
                    "max_transactions": 1000000,
                },
            ))
    print(f"  Seeded {len(DEVICE_MODELS)} device models")
