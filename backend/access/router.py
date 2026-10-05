"""Access control endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.deps import get_current_user
from access.models import AccessGroup

router = APIRouter()


@router.get("/groups")
async def list_groups(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(AccessGroup).where(AccessGroup.tenant_id == current_user.tenant_id))
    return list(result.scalars().all())
