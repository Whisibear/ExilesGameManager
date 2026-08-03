from app.services import activity_center, instance_store


def test_port_allocator_avoids_all_instance_ports():
    instances = [{"id": "a", "gamePort": 8211, "rconPort": 8212, "queryPort": 8213}]
    assert instance_store.allocate_instance_ports(instances, game_port=8211, rest_port=8212) == (8214, 8215, 8216)


def test_activity_traceback_is_hidden_from_operator_message():
    row = {
        "source": "Task Queue",
        "message": "Workshop failed\nTraceback (most recent call last):\nsecret path",
    }
    decorated = activity_center._decorate(row, "task", "task.failed")
    assert decorated["message"] == "Workshop failed"
