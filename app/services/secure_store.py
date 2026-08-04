"""Windows DPAPI-backed local secret storage.

Secrets are encrypted for the current Windows user and stored only under
%LOCALAPPDATA%\\ExilesGameManager\\oauth. No secret value is exported to GitHub,
logs, diagnostics or release metadata.
"""

from __future__ import annotations

import ctypes
import json
import os
from ctypes import wintypes
from pathlib import Path
from typing import Any

from app.paths import oauth_dir


class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _blob(data: bytes) -> tuple[DATA_BLOB, Any]:
    buffer = ctypes.create_string_buffer(data)
    return DATA_BLOB(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))), buffer


def _protect(data: bytes) -> bytes:
    if os.name != "nt":
        return data
    in_blob, _buffer = _blob(data)
    out_blob = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)
    ):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)


def _unprotect(data: bytes) -> bytes:
    if os.name != "nt":
        return data
    in_blob, _buffer = _blob(data)
    out_blob = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)
    ):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)


def _path(name: str) -> Path:
    if not name.replace("_", "").replace("-", "").isalnum():
        raise ValueError("Invalid secure-store name")
    return oauth_dir() / f"{name}.dat"


def save(name: str, value: dict[str, Any]) -> None:
    payload = json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    path = _path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_bytes(_protect(payload))
    os.replace(temp, path)


def load(name: str) -> dict[str, Any] | None:
    path = _path(name)
    if not path.exists():
        return None
    try:
        return json.loads(_unprotect(path.read_bytes()).decode("utf-8"))
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError):
        return None


def delete(name: str) -> None:
    _path(name).unlink(missing_ok=True)
