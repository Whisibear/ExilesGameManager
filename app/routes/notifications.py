from fastapi import APIRouter, Depends, HTTPException
from app.auth_deps import get_current_user, require_super_admin
from app.services import notification_center

router = APIRouter()

def _identity(user):
    return str(user.get("username") or "unknown"), str(user.get("role") or "admin")

@router.get("")
async def list_notifications(unreadOnly: bool = False, limit: int = 100, user=Depends(get_current_user)):
    username, role = _identity(user)
    return {"notifications": notification_center.list_notifications(username, role, unread_only=unreadOnly, limit=limit), "unreadCount": notification_center.unread_count(username, role)}

@router.post("/{notification_id}/read")
async def mark_read(notification_id: str, user=Depends(get_current_user)):
    username, _ = _identity(user)
    if not notification_center.mark_read(notification_id, username):
        raise HTTPException(status_code=404, detail="Notification not found or already read.")
    return {"ok": True}

@router.post("/read-all")
async def mark_all_read(user=Depends(get_current_user)):
    username, role = _identity(user)
    return {"updated": notification_center.mark_all_read(username, role)}

@router.delete("/read")
async def clear_read(user=Depends(get_current_user)):
    username, role = _identity(user)
    return {"deleted": notification_center.clear_read(username, role)}
