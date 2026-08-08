from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth_deps import get_current_user
from app.games.providers import (
    ProviderUnavailableError,
    get_provider_for_instance,
)
from app.games.providers.base import ServerSettingsProvider
from app.services import activity_log, instance_store

router = APIRouter()

_REDACTED = "••••••••"


def _require_active_instance() -> dict[str, Any]:
    instance = instance_store.get_active()
    if not instance:
        raise HTTPException(status_code=400, detail="No server selected. Create or import one in Settings.")
    return instance


def _settings_provider(
    instance: dict[str, Any],
) -> ServerSettingsProvider:
    try:
        return get_provider_for_instance(instance).settings
    except ProviderUnavailableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def _redact_credentials(
    fields: list[dict[str, Any]],
    user: dict[str, Any],
    provider: ServerSettingsProvider,
) -> list[dict[str, Any]]:
    if user["role"] == "super_admin":
        return fields
    return [
        {**field, "value": _REDACTED}
        if field["key"] in provider.credential_fields or bool(field.get("sensitive"))
        else field
        for field in fields
        if field["key"] not in provider.restricted_fields
    ]


def _settings_view(
    instance: dict[str, Any],
    user: dict[str, Any],
    provider: ServerSettingsProvider | None = None,
) -> dict[str, Any]:
    resolved = provider or _settings_provider(instance)
    fields = resolved.read_fields(instance)
    game = instance_store.get_game_definition(instance)
    return {
        "fields": _redact_credentials(fields, user, resolved),
        "gameId": game.id,
        "gameFamily": game.family,
        "gameEdition": game.edition,
        "gameLabel": game.label,
        "providerId": resolved.game_id,
        "restartRequired": False,
        "changedKeys": [],
    }


@router.get("")
async def get_settings(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    instance = _require_active_instance()
    provider = _settings_provider(instance)
    return _settings_view(instance, user, provider)


class UpdateSettingsRequest(BaseModel):
    values: dict[str, Any]


@router.post("")
async def update_settings(
    body: UpdateSettingsRequest, user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    instance = _require_active_instance()
    provider = _settings_provider(instance)
    value_keys = body.values.keys()
    current_fields = {field["key"]: field for field in provider.read_fields(instance)}
    sensitive_keys = provider.credential_fields | frozenset(
        key for key, field in current_fields.items() if field.get("sensitive")
    )
    if (
        user["role"] != "super_admin"
        and sensitive_keys & value_keys
    ):
        raise HTTPException(
            status_code=403,
            detail="Only the super admin can change server credentials.",
        )
    if (
        user["role"] != "super_admin"
        and provider.restricted_fields & value_keys
    ):
        raise HTTPException(
            status_code=403,
            detail="Only the super admin can change local management settings.",
        )
    before_fields = {field["key"]: field for field in provider.read_fields(instance)}
    try:
        provider.write_fields(instance, body.values)
        provider.synchronize_instance_metadata(instance, body.values)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    after_fields = {field["key"]: field for field in provider.read_fields(instance)}
    changed_keys = [
        key for key in body.values
        if key in after_fields and before_fields.get(key, {}).get("value") != after_fields[key].get("value")
    ]
    updated_instance = instance_store.get(instance["id"]) or instance
    response = _settings_view(updated_instance, user, provider)
    game = instance_store.get_game_definition(updated_instance)
    if game.family == "conan_exiles" and changed_keys:
        sensitive = {key for key, field in after_fields.items() if field.get("sensitive")}
        public_keys = [key for key in changed_keys if key not in sensitive]
        sensitive_count = len(changed_keys) - len(public_keys)
        parts = []
        if public_keys:
            parts.append(", ".join(public_keys))
        if sensitive_count:
            parts.append(f"{sensitive_count} sensitive setting(s)")
        activity_log.log(
            "info",
            updated_instance.get("name") or game.label,
            "Conan server settings saved: " + "; ".join(parts) + ". Restart required to apply changes.",
            instance_id=updated_instance["id"],
        )
        response["restartRequired"] = True
        response["changedKeys"] = changed_keys
    return response
