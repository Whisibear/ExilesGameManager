from __future__ import annotations

import time
from typing import Any

import httpx
from fastapi import HTTPException

from app.services import nexus_identity, secure_store

_STORE_NAME = "nexus_oauth"
_CLIENT_ID = "exiles_game_manager_egm"
_TOKEN_URL = "https://users.nexusmods.com/oauth/token"


def get_record() -> dict[str, Any]:
    record = secure_store.load(_STORE_NAME) or {"connected": False}
    if record.get("connected") and record.get("via") != "oauth_pkce":
        disconnect()
        return {"connected": False}
    return record


def save_oauth_record(token: dict[str, Any], account: dict[str, Any]) -> None:
    expires_in = int(token.get("expires_in") or 3600)
    secure_store.save(
        _STORE_NAME,
        {
            "connected": True,
            "via": "oauth_pkce",
            "accessToken": token["access_token"],
            "refreshToken": token.get("refresh_token"),
            "tokenType": token.get("token_type") or "Bearer",
            "expiresAt": int(time.time()) + max(60, expires_in - 30),
            "username": account.get("name"),
            "userId": account.get("user_id"),
            "isPremium": bool(account.get("is_premium")),
            "membershipRoles": list(account.get("membership_roles") or []),
            "premiumExpiry": account.get("premium_expiry"),
            "lastAccountSyncAt": int(time.time()),
        },
    )


def account_view() -> dict[str, Any]:
    record = get_record()
    if not record.get("connected"):
        return {"connected": False}
    username = record.get("username") or "?"
    return {
        "connected": True,
        "via": "oauth_pkce",
        "username": username,
        "userId": record.get("userId"),
        "isPremium": bool(record.get("isPremium")),
        "membershipRoles": list(record.get("membershipRoles") or []),
        "premiumExpiry": record.get("premiumExpiry"),
        "lastAccountSyncAt": record.get("lastAccountSyncAt"),
        "avatarInitial": username[:1].upper(),
    }


async def _refresh(record: dict[str, Any]) -> dict[str, Any]:
    refresh_token = record.get("refreshToken")
    if not refresh_token:
        disconnect()
        raise HTTPException(status_code=400, detail="The Nexus Mods session expired. Connect again.")
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            _TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": _CLIENT_ID,
                "refresh_token": refresh_token,
            },
            headers={"Accept": "application/json"},
        )
    if response.status_code >= 400:
        disconnect()
        raise HTTPException(status_code=400, detail="The Nexus Mods session could not be refreshed. Connect again.")
    token = response.json()
    access_token = token.get("access_token")
    if not access_token:
        disconnect()
        raise HTTPException(status_code=400, detail="Nexus Mods returned an invalid refresh response.")
    expires_in = int(token.get("expires_in") or 3600)
    account = nexus_identity.account_from_access_token(str(access_token))
    record.update(
        {
            "accessToken": access_token,
            "refreshToken": token.get("refresh_token") or refresh_token,
            "tokenType": token.get("token_type") or "Bearer",
            "expiresAt": int(time.time()) + max(60, expires_in - 30),
            "username": account.get("name") or record.get("username"),
            "userId": account.get("user_id") or record.get("userId"),
            "isPremium": bool(account.get("is_premium")),
            "membershipRoles": list(account.get("membership_roles") or []),
            "premiumExpiry": account.get("premium_expiry"),
            "lastAccountSyncAt": int(time.time()),
        }
    )
    secure_store.save(_STORE_NAME, record)
    return record


async def synchronize_account(*, force_refresh: bool = False) -> dict[str, Any]:
    record = get_record()
    if not record.get("connected") or not record.get("accessToken"):
        return {"connected": False}

    now = int(time.time())
    last_sync = int(record.get("lastAccountSyncAt") or 0)
    should_refresh = (
        force_refresh
        or int(record.get("expiresAt") or 0) <= now
        or now - last_sync >= 60
    )

    if should_refresh and record.get("refreshToken"):
        record = await _refresh(record)
    else:
        account = nexus_identity.account_from_access_token(str(record["accessToken"]))
        record.update(
            {
                "username": account.get("name") or record.get("username"),
                "userId": account.get("user_id") or record.get("userId"),
                "isPremium": bool(account.get("is_premium")),
                "membershipRoles": list(account.get("membership_roles") or []),
                "premiumExpiry": account.get("premium_expiry"),
            }
        )
        secure_store.save(_STORE_NAME, record)

    return account_view()

async def require_access_token() -> str:
    record = get_record()
    if not record.get("connected") or not record.get("accessToken"):
        raise HTTPException(status_code=400, detail="Connect Nexus Mods in Super Admin first.")
    if int(record.get("expiresAt") or 0) <= int(time.time()):
        record = await _refresh(record)
    return str(record["accessToken"])


async def require_premium_access_token() -> str:
    account = await synchronize_account(force_refresh=True)
    record = get_record()
    token = await require_access_token()
    if not account.get("isPremium") or not record.get("isPremium"):
        raise HTTPException(
            status_code=403,
            detail="Nexus Mods Premium is required for automatic direct downloads.",
        )
    return token


def disconnect() -> None:
    secure_store.delete(_STORE_NAME)
