"""Covers app/services/system_settings.py's configurable admin panel port
(TICKET-0171) and the route that exposes it.
"""

import pytest

from app.services import system_settings


def test_get_admin_port_defaults_to_8000():
    assert system_settings.get_admin_port() == system_settings.DEFAULT_ADMIN_PORT


def test_update_config_persists_admin_port():
    system_settings.update_config(
        boot_with_windows=False, auto_start_active_server=False, privacy_mode=False, admin_port=9001
    )
    assert system_settings.get_admin_port() == 9001
    assert system_settings.get_config()["adminPort"] == 9001


@pytest.mark.parametrize("bad_port", [80, 1023, 65536, 100000, 0, -1])
def test_update_config_rejects_out_of_range_port(bad_port):
    with pytest.raises(ValueError):
        system_settings.update_config(
            boot_with_windows=False, auto_start_active_server=False, privacy_mode=False, admin_port=bad_port
        )
    # A rejected update must not have partially saved.
    assert system_settings.get_admin_port() == system_settings.DEFAULT_ADMIN_PORT


def test_route_rejects_invalid_admin_port(super_admin):
    resp = super_admin["client"].post(
        "/api/system-settings",
        json={"bootWithWindows": False, "autoStartActiveServer": False, "privacyMode": False, "adminPort": 80},
    )
    assert resp.status_code == 400


def test_route_saves_valid_admin_port(super_admin):
    resp = super_admin["client"].post(
        "/api/system-settings",
        json={"bootWithWindows": False, "autoStartActiveServer": False, "privacyMode": False, "adminPort": 9001},
    )
    assert resp.status_code == 200
    assert resp.json()["adminPort"] == 9001
