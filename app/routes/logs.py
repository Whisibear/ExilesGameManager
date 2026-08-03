from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth_deps import get_current_user
from app.services import activity_log, app_event_log, instance_store, privacy, runtime_logging

router = APIRouter()


@router.get("")
async def get_logs() -> list[dict[str, Any]]:
    return activity_log.get_for_instance(instance_store.get_active_id())


@router.get("/streams")
async def get_log_streams(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return {
        "app": app_event_log.get_all(mask_ips=user.get("role") != "super_admin" or privacy.is_enabled()),
        "activity": activity_log.get_for_instance(instance_store.get_active_id()),
    }


class FrontendEvent(BaseModel):
    level: str = "error"
    message: str = Field(min_length=1, max_length=8000)
    source: str = Field(default="Browser", max_length=200)
    stack: str | None = Field(default=None, max_length=20000)
    url: str | None = Field(default=None, max_length=2000)


@router.post("/frontend-event", status_code=204)
async def frontend_event(event: FrontendEvent) -> None:
    runtime_logging.write_http_event({
        "type": "frontend",
        "level": event.level,
        "source": event.source,
        "message": privacy.scrub_text(event.message),
        "stack": privacy.scrub_text(event.stack or ""),
        "url": event.url,
    })
    app_event_log.log(event.level, f"Frontend: {event.source}", event.message, stack=event.stack, url=event.url)
