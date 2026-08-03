from pathlib import Path

import pytest

from app.services import palworld_settings


def _make_server(tmp_path: Path) -> Path:
    server = tmp_path / "Server"
    ini = server / "Pal" / "Saved" / "Config" / "WindowsServer" / "PalWorldSettings.ini"
    ini.parent.mkdir(parents=True)
    ini.write_text(
        "[/Script/Pal.PalGameWorldSettings]\n"
        "OptionSettings=(DayTimeSpeedRate=1.000000,ExpRate=2.000000)\n",
        encoding="utf-8",
    )
    return server


@pytest.mark.parametrize("entered, expected", [("0,5", "0.500000"), ("0.5", "0.500000"), (2, "2.000000")])
def test_write_settings_accepts_comma_or_dot_decimal(tmp_path: Path, entered, expected: str) -> None:
    server = _make_server(tmp_path)
    palworld_settings.write_settings(server, {"DayTimeSpeedRate": entered})
    text = (
        server / "Pal" / "Saved" / "Config" / "WindowsServer" / "PalWorldSettings.ini"
    ).read_text(encoding="utf-8")
    assert f"DayTimeSpeedRate={expected}" in text
    assert "ExpRate=2.000000" in text


@pytest.mark.parametrize("entered", ["", "1,2.3", "abc", "1,2,3"])
def test_write_settings_rejects_invalid_decimal(tmp_path: Path, entered: str) -> None:
    server = _make_server(tmp_path)
    with pytest.raises(ValueError):
        palworld_settings.write_settings(server, {"DayTimeSpeedRate": entered})
