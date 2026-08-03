"""Covers app/routes/network.py's admin-port-aware firewall rule naming
(TICKET-0171). The admin panel port used to be a fixed constant, so its
Windows Firewall rule had one fixed name ("ExilesGameManager") - once the port
became configurable, reusing that same fixed name for any port would make a
rule created for an old port look like "already allowed" for a newly
configured port that isn't actually covered by it at all.

Only the pure naming helper is tested here, not firewall.rule_exists()/
add_inbound_rule() themselves - those shell out to netsh/a UAC-elevated
helper and would attempt to actually query or modify this machine's real
Windows Firewall, which isn't appropriate for an automated test.
"""

from app.routes import network
from app.services import system_settings


def test_admin_firewall_rule_name_uses_fixed_name_at_default_port():
    assert network._admin_firewall_rule_name(system_settings.DEFAULT_ADMIN_PORT) == network.ADMIN_FIREWALL_RULE_NAME


def test_admin_firewall_rule_name_is_port_specific_when_changed():
    name = network._admin_firewall_rule_name(9001)
    assert name != network.ADMIN_FIREWALL_RULE_NAME
    assert "9001" in name


def test_admin_firewall_rule_name_differs_between_non_default_ports():
    assert network._admin_firewall_rule_name(9001) != network._admin_firewall_rule_name(9002)
