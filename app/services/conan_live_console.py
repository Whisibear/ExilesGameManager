
from __future__ import annotations

from pathlib import Path
from typing import Any


LOG_RELATIVE_PATH = Path("ConanSandbox") / "Saved" / "Logs" / "ConanSandbox.log"
_MAX_READ_BYTES = 256 * 1024
_DEFAULT_INITIAL_BYTES = 64 * 1024


def log_path(instance: dict[str, Any]) -> Path:
    return Path(instance["serverPath"]) / LOG_RELATIVE_PATH


def read_chunk(
    instance: dict[str, Any],
    cursor: int | None = None,
    *,
    max_bytes: int = _MAX_READ_BYTES,
) -> dict[str, Any]:
    path = log_path(instance)
    if not path.is_file():
        return {
            "cursor": 0,
            "text": "",
            "reset": cursor not in (None, 0),
            "available": False,
            "path": str(path),
        }

    size = path.stat().st_size
    reset = False

    if cursor is None:
        start = max(0, size - min(_DEFAULT_INITIAL_BYTES, max_bytes))
    else:
        start = max(0, int(cursor))
        if start > size:
            start = 0
            reset = True

    remaining = max(0, size - start)
    if remaining > max_bytes:
        start = size - max_bytes
        reset = True

    with path.open("rb") as handle:
        handle.seek(start)
        data = handle.read(max_bytes)
        end = handle.tell()

    return {
        "cursor": end,
        "text": data.decode("utf-8", errors="replace"),
        "reset": reset,
        "available": True,
        "path": str(path),
    }
