from fastapi import APIRouter, Depends
from app.auth_deps import get_current_user
from app.services import activity_center, privacy

router = APIRouter()

@router.get("")
async def list_activity(instanceId: str | None = None, category: str | None = None, level: str | None = None, q: str | None = None, limit: int = 300, user=Depends(get_current_user)):
    return {"events": activity_center.list_events(instance_id=instanceId, category=category, level=level, query=q, limit=limit, mask_ips=user.get("role") != "super_admin" or privacy.is_enabled())}
