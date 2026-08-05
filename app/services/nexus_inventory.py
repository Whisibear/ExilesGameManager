from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.services import instance_storage

_STORE_NAME = "nexus_inventory"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def load(instance_id: str) -> list[dict[str, Any]]:
    value = instance_storage.load(instance_id, _STORE_NAME, [])
    return value if isinstance(value, list) else []


def save(instance_id: str, entries: list[dict[str, Any]]) -> None:
    instance_storage.save(instance_id, _STORE_NAME, entries)


def _paths(entry: dict[str, Any]) -> set[str]:
    values = [entry.get("sourcePath"), entry.get("deployedPath"), *(entry.get("installedPaths") or [])]
    return {str(Path(str(value)).resolve()).lower() for value in values if value}


def upsert(instance_id: str, entry: dict[str, Any]) -> dict[str, Any]:
    entries = load(instance_id)
    mod_id = int(entry.get("nexusModId") or entry.get("sourceModId") or 0)
    file_id = int(entry.get("nexusFileId") or 0)
    paths = _paths(entry)
    selected = None
    for current in entries:
        current_mod_id = int(current.get("nexusModId") or current.get("sourceModId") or 0)
        current_file_id = int(current.get("nexusFileId") or 0)
        if mod_id and current_mod_id == mod_id and (not file_id or current_file_id == file_id):
            selected = current
            break
        if paths and paths & _paths(current):
            selected = current
            break
    merged = dict(selected or {})
    merged.update({key: value for key, value in entry.items() if value is not None})
    merged["nexusModId"] = mod_id or merged.get("nexusModId")
    merged["sourceModId"] = mod_id or merged.get("sourceModId")
    merged["nexusFileId"] = file_id or merged.get("nexusFileId")
    merged["updatedAt"] = _now()
    merged.setdefault("installedAt", _now())
    if selected is None:
        entries.append(merged)
    else:
        entries = [merged if current is selected else current for current in entries]
    save(instance_id, entries)
    return merged


def remove(instance_id: str, *, mod_id: int = 0, record_id: str | None = None) -> None:
    entries = load(instance_id)
    entries = [
        entry for entry in entries
        if not ((record_id and str(entry.get("id") or "") == record_id)
                or (mod_id and int(entry.get("nexusModId") or entry.get("sourceModId") or 0) == mod_id))
    ]
    save(instance_id, entries)


def find_match(instance_id: str, record: dict[str, Any]) -> dict[str, Any] | None:
    mod_id = int(record.get("nexusModId") or record.get("sourceModId") or 0)
    paths = _paths(record)
    normalized_name = "".join(ch for ch in str(record.get("name") or "").lower() if ch.isalnum())
    for entry in load(instance_id):
        current_mod_id = int(entry.get("nexusModId") or entry.get("sourceModId") or 0)
        if mod_id and current_mod_id == mod_id:
            return entry
        if paths and paths & _paths(entry):
            return entry
        entry_name = "".join(ch for ch in str(entry.get("name") or "").lower() if ch.isalnum())
        if normalized_name and entry_name == normalized_name:
            return entry
    return None
