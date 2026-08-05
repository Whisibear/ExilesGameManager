"""Nexus Mods OAuth 2.0 Authorization Code flow with PKCE."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import secrets
import time
import urllib.parse
import uuid
from typing import Any

import httpx

from app.services import nexus_identity, nexus_session

logger = logging.getLogger("egm.nexus_oauth")

CLIENT_ID = "exiles_game_manager_egm"
REDIRECT_URI = "http://127.0.0.1:8000/api/nexus/oauth/callback"
AUTHORIZE_URL = "https://users.nexusmods.com/oauth/authorize"
TOKEN_URL = "https://users.nexusmods.com/oauth/token"
SESSION_TTL_SECONDS = 5 * 60

_pending: dict[str, dict[str, Any]] = {}


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def start() -> dict[str, str]:
    request_id = str(uuid.uuid4())
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = _base64url(hashlib.sha256(verifier.encode("ascii")).digest())
    _pending[request_id] = {
        "state": state,
        "verifier": verifier,
        "status": "pending",
        "createdAt": time.time(),
    }
    query = urllib.parse.urlencode(
        {
            "client_id": CLIENT_ID,
            "response_type": "code",
            "scope": "",
            "redirect_uri": REDIRECT_URI,
            "state": state,
            "code_challenge_method": "S256",
            "code_challenge": challenge,
        }
    )
    return {"requestId": request_id, "authorizeUrl": f"{AUTHORIZE_URL}?{query}"}




def _safe_oauth_error(response: httpx.Response) -> str:
    """Return useful OAuth error details without exposing tokens or secrets."""
    error_code = None
    description = None
    try:
        payload = response.json()
        if isinstance(payload, dict):
            error_code = payload.get("error")
            description = payload.get("error_description") or payload.get("message")
    except (ValueError, json.JSONDecodeError):
        payload = None

    details = [f"HTTP {response.status_code}"]
    if error_code:
        details.append(str(error_code))
    if description:
        details.append(str(description)[:300])
    return " - ".join(details)

def _find_by_state(state: str) -> tuple[str, dict[str, Any]] | None:
    now = time.time()
    expired = [key for key, value in _pending.items() if now - value["createdAt"] > SESSION_TTL_SECONDS]
    for key in expired:
        _pending.pop(key, None)
    for request_id, session in _pending.items():
        if secrets.compare_digest(session["state"], state):
            return request_id, session
    return None


async def complete_callback(code: str | None, state: str | None, error: str | None) -> str:
    if not state:
        return "Nexus Mods authorization failed: missing state. You may close this window."
    match = _find_by_state(state)
    if not match:
        return "Nexus Mods authorization request expired or is invalid. Return to EGM and try again."
    request_id, session = match
    if error:
        session.update({"status": "error", "error": error})
        return "Nexus Mods authorization was cancelled. You may close this window."
    if not code:
        session.update({"status": "error", "error": "Missing authorization code."})
        return "Nexus Mods authorization failed. You may close this window."

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "redirect_uri": REDIRECT_URI,
                    "client_id": CLIENT_ID,
                    "code": code,
                    "code_verifier": session["verifier"],
                },
                headers={"Accept": "application/json"},
            )
        if response.status_code >= 400:
            details = _safe_oauth_error(response)
            logger.warning("Nexus OAuth token exchange rejected: %s", details)
            raise RuntimeError(f"Nexus token exchange failed: {details}.")

        try:
            token = response.json()
        except ValueError as exc:
            raise RuntimeError("Nexus token endpoint returned invalid JSON.") from exc

        if not isinstance(token, dict):
            raise RuntimeError("Nexus token endpoint returned an invalid response.")

        access_token = token.get("access_token")
        if not access_token:
            available_fields = ", ".join(sorted(str(key) for key in token.keys()))
            logger.warning(
                "Nexus OAuth token response contained no access token; fields=%s",
                available_fields or "<none>",
            )
            raise RuntimeError("Nexus token response did not contain an access token.")

        account = nexus_identity.account_from_access_token(str(access_token))
        logger.info(
            "Nexus OAuth token accepted for account=%s user_id=%s premium=%s roles=%s claim_keys=%s user_claim_keys=%s",
            account.get("name"),
            account.get("user_id"),
            account.get("is_premium"),
            account.get("membership_roles"),
            account.get("claim_keys"),
            account.get("user_claim_keys"),
        )
        nexus_session.save_oauth_record(token, account)
        session.update({"status": "connected"})
        return f"Nexus Mods connected as {account.get('name') or 'user'}. You may close this window."
    except Exception as exc:
        logger.warning("Nexus OAuth callback failed: %s", exc)
        session.update({"status": "error", "error": str(exc)})
        return "Nexus Mods authorization failed. Return to EGM for details."


def get_status(request_id: str) -> dict[str, Any] | None:
    session = _pending.get(request_id)
    if not session:
        return None
    if time.time() - session["createdAt"] > SESSION_TTL_SECONDS:
        _pending.pop(request_id, None)
        return None
    status = session["status"]
    if status == "pending":
        return {"status": "pending"}
    if status == "error":
        message = session.get("error") or "Nexus Mods authorization failed."
        _pending.pop(request_id, None)
        return {"status": "error", "message": message}
    _pending.pop(request_id, None)
    return {"status": "connected", "account": nexus_session.account_view()}
