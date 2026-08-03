from app.services import firewall


def test_instance_rules_are_named_and_protocol_specific():
    rules = firewall.instance_rules({
        "id": "srv-1", "name": "Second Server", "gamePort": 8213,
        "rconPort": 8214, "queryPort": 27016, "useQueryPort": True,
    })
    assert [(r.port, r.protocol) for r in rules] == [(8213, "UDP"), (27016, "UDP"), (8214, "TCP")]
    assert all("Second Server" in r.name for r in rules)


def test_instance_rules_skip_query_when_disabled():
    rules = firewall.instance_rules({"name": "Clean", "gamePort": 8211, "rconPort": 8212, "useQueryPort": False})
    assert len(rules) == 2
