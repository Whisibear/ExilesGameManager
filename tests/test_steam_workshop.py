import json
from pathlib import Path

import pytest

from app.services import pal_mod_settings, steam_workshop


def test_parse_workshop_url_and_id() -> None:
    assert steam_workshop.parse_workshop_id("1234567890") == "1234567890"
    assert (
        steam_workshop.parse_workshop_id(
            "https://steamcommunity.com/sharedfiles/filedetails/?id=1234567890&searchtext=test"
        )
        == "1234567890"
    )


def test_parse_workshop_id_rejects_unsafe_values() -> None:
    with pytest.raises(steam_workshop.WorkshopError):
        steam_workshop.parse_workshop_id("../Workshop")


def test_pal_mod_settings_round_trip(tmp_path: Path) -> None:
    pal_mod_settings.write_active_mods(tmp_path, ["Alpha", "Beta", "Alpha"])
    assert pal_mod_settings.active_mods(tmp_path) == ["Alpha", "Beta"]
    pal_mod_settings.set_enabled(tmp_path, "Alpha", False)
    assert pal_mod_settings.active_mods(tmp_path) == ["Beta"]


def test_inspect_installed_workshop_mod(tmp_path: Path) -> None:
    mod_dir = tmp_path / "Mods" / "Workshop" / "1234567890"
    mod_dir.mkdir(parents=True)
    (mod_dir / "Info.json").write_text(
        json.dumps({"PackageName": "Example.Mod", "IsServer": True, "InstallRules": []}), encoding="utf-8"
    )
    result = steam_workshop.inspect_installed(tmp_path, "1234567890")
    assert result["packageName"] == "Example.Mod"


def test_workshop_auth_is_super_admin_only_and_never_builds_login_args_in_routes() -> None:
    route_source = (Path(__file__).parents[1] / "app" / "routes" / "mods" / "workshop.py").read_text(encoding="utf-8")
    assert 'dependencies=[Depends(require_super_admin)]' in route_source
    assert "+login" not in route_source


def test_steamcmd_redacts_non_anonymous_password() -> None:
    from app.services import steamcmd

    args = ["steamcmd.exe", "+login", "user", "secret", "+quit"]
    redacted = steamcmd._redact_args(args)
    assert redacted == ["steamcmd.exe", "+login", "<steam-user>", "********", "+quit"]
    assert args[3] == "secret"


def test_steamcmd_keeps_anonymous_command_intact() -> None:
    from app.services import steamcmd

    args = ["steamcmd.exe", "+login", "anonymous", "+quit"]
    assert steamcmd._redact_args(args) == args

@pytest.mark.asyncio
async def test_update_all_creates_compact_backup_and_never_starts_server(monkeypatch, tmp_path):
    from app.services import steam_workshop

    server = tmp_path / "server"
    (server / "Pal" / "Saved" / "Config").mkdir(parents=True)
    (server / "Pal" / "Saved" / "Config" / "PalWorldSettings.ini").write_text("x", encoding="utf-8")
    (server / "Mods").mkdir()
    (server / "Mods" / "PalModSettings.ini").write_text("x", encoding="utf-8")
    instance = {"id": "x", "name": "Test", "serverPath": str(server)}

    monkeypatch.setattr(steam_workshop, "check_updates", lambda instance: None)
    async def fake_check(instance):
        return {"mods": [{"workshopId": "3769942146", "updateAvailable": True}]}
    monkeypatch.setattr(steam_workshop, "check_updates", fake_check)
    async def fake_details(workshop_id):
        return {"workshopId": workshop_id, "title": "Test", "timeUpdated": 1}
    async def fake_download(workshop_id, *, server_path=None, force=False):
        assert force is True
        return tmp_path / "download"
    monkeypatch.setattr(steam_workshop, "get_details", fake_details)
    monkeypatch.setattr(steam_workshop, "download", fake_download)
    monkeypatch.setattr(steam_workshop, "install_from_download", lambda instance, details, path: {
        "id": "workshop-3769942146", "workshopId": "3769942146", "packageName": "Test",
        "status": "enabled", "loadPriority": 1, "name": "Test"
    })
    monkeypatch.setattr(steam_workshop.mods_store, "save_mods", lambda instance_id, mods: None)
    monkeypatch.setattr(steam_workshop.mods_store, "sorted_mods", lambda mods: mods)
    monkeypatch.setattr(steam_workshop, "discover_installed", lambda instance, mods: [])
    monkeypatch.setattr(steam_workshop.mods_store, "load_mods", lambda instance_id: [])
    async def fake_status(mods, instance=None):
        return mods
    monkeypatch.setattr(steam_workshop, "with_update_status", fake_status)
    monkeypatch.setattr(steam_workshop.backup_service.instance_store, "instance_dir", lambda instance_id: tmp_path / "data")

    result = await steam_workshop.update_all(instance)
    assert result["updated"] == 1
    backup = Path(result["backup"]["folder"])
    assert (backup / "Pal" / "Saved" / "Config" / "PalWorldSettings.ini").is_file()
    assert (backup / "Mods" / "PalModSettings.ini").is_file()
    assert not (backup / "Pal" / "Binaries").exists()
