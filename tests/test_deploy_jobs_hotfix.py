import asyncio
from pathlib import Path

from app.services import deploy_jobs


def test_clean_clone_does_not_forward_template_path(monkeypatch, tmp_path: Path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    (source / "DefaultPalWorldSettings.ini").write_text(
        "[/Script/Pal.PalGameWorldSettings]\nOptionSettings=()\n",
        encoding="utf-8",
    )

    captured = {}

    def fake_initialize(server_path, **kwargs):
        captured["server_path"] = server_path
        captured["kwargs"] = kwargs

    monkeypatch.setattr(deploy_jobs.palworld_settings, "initialize_settings", fake_initialize)
    monkeypatch.setattr(
        deploy_jobs.instance_store,
        "create_instance",
        lambda **kwargs: {"id": "instance-1", **kwargs},
    )
    monkeypatch.setattr(
        deploy_jobs.firewall,
        "sync_instance",
        lambda instance: {"created": []},
    )

    job_id = "deploy-test-clean-clone"
    deploy_jobs._jobs[job_id] = {
        "status": "running",
        "log": [],
        "error": None,
        "instanceId": None,
    }

    asyncio.run(
        deploy_jobs._run_deploy(
            job_id,
            name="Clone",
            install_dir=target,
            game_port=8213,
            rcon_port=8214,
            max_players=32,
            template_path=source,
        )
    )

    assert deploy_jobs._jobs[job_id]["status"] == "done"
    assert captured["server_path"] == target
    assert "template_path" not in captured["kwargs"]


def test_unexpected_deploy_error_becomes_terminal_error(monkeypatch, tmp_path: Path):
    target = tmp_path / "target"

    async def fake_install(*args, **kwargs):
        return None

    def fail_initialize(*args, **kwargs):
        raise TypeError("simulated programming error")

    monkeypatch.setattr(deploy_jobs.steamcmd, "install_palserver", fake_install)
    monkeypatch.setattr(deploy_jobs.palworld_settings, "initialize_settings", fail_initialize)

    job_id = "deploy-test-error-state"
    deploy_jobs._jobs[job_id] = {
        "status": "running",
        "log": [],
        "error": None,
        "instanceId": None,
    }

    asyncio.run(
        deploy_jobs._run_deploy(
            job_id,
            name="Broken",
            install_dir=target,
            game_port=8211,
            rcon_port=8212,
            max_players=32,
        )
    )

    job = deploy_jobs._jobs[job_id]
    assert job["status"] == "error"
    assert "simulated programming error" in job["error"]
    assert any("ERROR:" in line for line in job["log"])
