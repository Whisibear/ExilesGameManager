import json
import os
import tempfile
from pathlib import Path
from typing import Any

from app.paths import data_dir

DATA_DIR = data_dir()


def _path(name: str) -> Path:
    return DATA_DIR / f"{name}.json"


def load(name: str, default: Any) -> Any:
    path = _path(name)
    if not path.exists():
        return default

    try:
        text = path.read_text(encoding="utf-8-sig")
        if not text.strip():
            return default
        return json.loads(text)
    except (OSError, UnicodeError, json.JSONDecodeError):
        backup = path.with_suffix(path.suffix + ".corrupt")
        try:
            if backup.exists():
                backup.unlink()
            path.replace(backup)
        except OSError:
            pass
        save(name, default)
        return default


def save(name: str, value: Any) -> None:
    path = _path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, ensure_ascii=False) + "\n"

    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
