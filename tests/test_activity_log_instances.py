from app.services import activity_log


def test_get_for_instance_isolates_new_and_legacy_entries(monkeypatch):
    instances = {
        "srv-test": {"id": "srv-test", "name": "Test"},
        "srv-test2": {"id": "srv-test2", "name": "Test2"},
    }
    monkeypatch.setattr("app.services.instance_store.get", lambda instance_id: instances.get(instance_id))
    monkeypatch.setattr(activity_log, "_loaded", True)
    activity_log._entries.clear()
    activity_log._entries.extend([
        {"id": "1", "timestamp": "2026-01-01T00:00:00", "level": "info", "source": "Test", "message": "legacy test"},
        {"id": "2", "timestamp": "2026-01-01T00:00:01", "level": "info", "source": "Test2", "message": "legacy test2"},
        {"id": "3", "timestamp": "2026-01-01T00:00:02", "level": "info", "source": "Renamed", "message": "new test", "instanceId": "srv-test"},
        {"id": "4", "timestamp": "2026-01-01T00:00:03", "level": "info", "source": "Test", "message": "new test2", "instanceId": "srv-test2"},
    ])

    assert [entry["id"] for entry in activity_log.get_for_instance("srv-test")] == ["3", "1"]
    assert [entry["id"] for entry in activity_log.get_for_instance("srv-test2")] == ["4", "2"]


def test_get_for_instance_returns_empty_for_missing_instance(monkeypatch):
    monkeypatch.setattr("app.services.instance_store.get", lambda _instance_id: None)
    assert activity_log.get_for_instance("missing") == []
