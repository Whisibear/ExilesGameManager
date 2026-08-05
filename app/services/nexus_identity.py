"""Safe mapping of Nexus Mods OAuth JWT claims to EGM account metadata."""
from __future__ import annotations

import base64
import json
import time
from collections.abc import Iterable, Mapping
from typing import Any

_PREMIUM_ROLES = {
    "premium",
    "lifetimepremium",
    "lifetime_premium",
    "lifetime-premium",
}


def decode_jwt_payload(access_token: str) -> dict[str, Any]:
    parts = access_token.split(".")
    if len(parts) != 3:
        raise RuntimeError("Nexus Mods returned an access token in an unexpected format.")

    encoded_payload = parts[1]
    padding = "=" * (-len(encoded_payload) % 4)
    try:
        payload = base64.urlsafe_b64decode(encoded_payload + padding)
        decoded = json.loads(payload.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Nexus Mods returned an unreadable access token.") from exc

    if not isinstance(decoded, dict):
        raise RuntimeError("Nexus Mods returned an invalid access-token payload.")
    return decoded


def _normalized_roles(value: Any) -> tuple[str, ...]:
    roles: list[str] = []

    if isinstance(value, str):
        candidates: Iterable[Any] = re_split_roles(value)
    elif isinstance(value, Mapping):
        candidates = [
            key
            for key, enabled in value.items()
            if enabled is True or str(enabled).strip().lower() in {"1", "true", "yes", "active"}
        ]
    elif isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        candidates = value
    else:
        candidates = ()

    for candidate in candidates:
        role = str(candidate).strip().lower().replace(" ", "_")
        if role and role not in roles:
            roles.append(role)
    return tuple(roles)


def re_split_roles(value: str) -> list[str]:
    normalized = value.replace(",", " ").replace(";", " ").replace("|", " ")
    return [part for part in normalized.split() if part]


def _truthy(value: Any) -> bool:
    if value is True:
        return True
    return str(value).strip().lower() in {
        "1",
        "true",
        "yes",
        "active",
        "premium",
        "lifetimepremium",
        "lifetime_premium",
        "lifetime-premium",
    }


def _future_timestamp(value: Any) -> bool:
    try:
        timestamp = float(value)
    except (TypeError, ValueError):
        return False

    if timestamp <= 0:
        return False

    # Nexus currently exposes Unix seconds; tolerate milliseconds defensively.
    if timestamp > 10_000_000_000:
        timestamp /= 1000
    return timestamp > time.time()


def account_from_access_token(access_token: str) -> dict[str, Any]:
    claims = decode_jwt_payload(access_token)
    user = claims.get("user")
    if not isinstance(user, dict):
        user = {}

    username = (
        user.get("username")
        or user.get("name")
        or claims.get("preferred_username")
        or claims.get("username")
        or claims.get("name")
        or "Nexus Mods user"
    )
    user_id = (
        user.get("user_id")
        or user.get("id")
        or claims.get("user_id")
        or claims.get("sub")
    )

    membership_roles = _normalized_roles(
        user.get("membership_roles")
        or user.get("membershipRoles")
        or user.get("roles")
        or claims.get("membership_roles")
        or claims.get("membershipRoles")
        or claims.get("roles")
    )

    explicit_premium_values = (
        user.get("is_premium"),
        user.get("isPremium"),
        user.get("premium"),
        claims.get("is_premium"),
        claims.get("isPremium"),
        claims.get("premium"),
    )
    premium_expiry = (
        user.get("premium_expiry")
        or user.get("premiumExpiry")
        or claims.get("premium_expiry")
        or claims.get("premiumExpiry")
    )

    is_premium = (
        any(role in _PREMIUM_ROLES for role in membership_roles)
        or any(_truthy(value) for value in explicit_premium_values)
        or _future_timestamp(premium_expiry)
    )

    return {
        "name": str(username),
        "user_id": user_id,
        "is_premium": is_premium,
        "membership_roles": list(membership_roles),
        "premium_expiry": premium_expiry,
        "claim_keys": sorted(str(key) for key in claims.keys()),
        "user_claim_keys": sorted(str(key) for key in user.keys()),
    }
