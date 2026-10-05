"""Notifications placeholder router."""
from fastapi import APIRouter, Depends
from core.deps import get_current_user
router = APIRouter()

@router.get("")
async def list_notifications(current_user=Depends(get_current_user)):
    return []
