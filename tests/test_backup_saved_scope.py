import asyncio
import json
from pathlib import Path

from app.services import backup_service


def test_snapshot_contains_complete_saved_directory(tmp_path, monkeypatch):
    server_root = tmp_path / "server"
    saved = server_root / "Pal" / "Saved"
    (saved / "SaveGames" / "0").mkdir(parents=True)
    (saved / "Config" / "WindowsServer").mkdir(parents=True)
    (saved / "SaveGames" / "0" / "Level.sav").write_bytes(b"world")
    (saved / "Config" / "WindowsServer" / "PalWorldSettings.ini").write_text("config", encoding="utf-8")

    backups = tmp_path / "instance"
    monkeypatch.setattr(backup_service.instance_store, "instance_dir", lambda _id: backups)
    monkeypatch.setattr(backup_service, "_prune_old_backups", lambda _id: None)

    record = asyncio.run(
        backup_service._create_snapshot(
            {"id": "srv-test", "name": "Test", "serverPath": str(server_root)},
            kind="manual",
        )
    )

    assert record is not None
    folder = Path(record["folder"])
    assert (folder / "Saved" / "SaveGames" / "0" / "Level.sav").read_bytes() == b"world"
    assert (
        folder / "Saved" / "Config" / "WindowsServer" / "PalWorldSettings.ini"
    ).read_text(encoding="utf-8") == "config"
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    assert any(entry["path"].startswith("Saved/Config/") for entry in meta["manifest"])
    assert any(entry["path"].startswith("Saved/SaveGames/") for entry in meta["manifest"])
