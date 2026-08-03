import asyncio
import importlib


def test_enqueue_cancel_and_persistence(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOPAL_DATA_DIR", str(tmp_path))
    from app.services import task_queue
    importlib.reload(task_queue)

    async def scenario():
        await task_queue.start()
        task = task_queue.enqueue("firewall.sync_all", title="Firewall")
        assert task["status"] == "queued"
        cancelled = task_queue.cancel(task["id"])
        assert cancelled["status"] == "cancelled"
        assert task_queue.get_task(task["id"])["status"] == "cancelled"
        await task_queue.stop()

    asyncio.run(scenario())
    assert (tmp_path / "task_queue.json").is_file()


def test_retry_creates_new_task(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOPAL_DATA_DIR", str(tmp_path))
    from app.services import task_queue
    importlib.reload(task_queue)

    async def scenario():
        await task_queue.start()
        original = task_queue.enqueue("firewall.sync_all", title="Firewall")
        task_queue.cancel(original["id"])
        retried = task_queue.retry(original["id"])
        assert retried["id"] != original["id"]
        assert retried["status"] == "queued"
        await task_queue.stop()

    asyncio.run(scenario())
