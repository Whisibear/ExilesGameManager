import asyncio

from app.services import app_update


def test_update_service_is_cleanly_unconfigured(monkeypatch):
    monkeypatch.delenv(app_update.REPOSITORY_ENV, raising=False)
    status = asyncio.run(app_update.get_status())
    assert status["configured"] is False
    assert status["available"] is False
    assert status["message"] == "Update service not configured."
