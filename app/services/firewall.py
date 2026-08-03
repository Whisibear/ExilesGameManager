"""Windows Firewall management with one normal UAC consent prompt.

On Windows 11 the desktop app may run unelevated; in that case all missing
rules are written to one temporary PowerShell script and started with
``-Verb RunAs``. Windows shows its standard consent dialog once. On Windows
Server 2022, when ExilesGameManager already runs elevated/as a service, rules are
applied directly without another prompt.
"""
from __future__ import annotations

import ctypes
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.services.windows_subprocess import hidden_process_kwargs

logger = logging.getLogger("egm.firewall")


class FirewallError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class FirewallRule:
    name: str
    port: int
    protocol: str


def _windows() -> bool:
    return os.name == "nt"


def is_elevated() -> bool:
    if not _windows():
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def rule_exists(rule_name: str) -> bool:
    if not _windows():
        return False
    result = subprocess.run(
        ["netsh", "advfirewall", "firewall", "show", "rule", f"name={rule_name}"],
        capture_output=True, text=True, timeout=10, **hidden_process_kwargs(),
    )
    text = (result.stdout + result.stderr).lower()
    return result.returncode == 0 and "no rules match" not in text and "keine regeln" not in text


def _validate(rule: FirewallRule) -> FirewallRule:
    protocol = rule.protocol.upper()
    if protocol not in {"TCP", "UDP"}:
        raise FirewallError("Protocol must be TCP or UDP.")
    if not 1 <= int(rule.port) <= 65535:
        raise FirewallError("Port must be between 1 and 65535.")
    return FirewallRule(rule.name.replace('"', "'"), int(rule.port), protocol)


def ensure_inbound_rules(rules: list[FirewallRule]) -> dict[str, object]:
    """Create all missing rules in one operation/UAC prompt."""
    normalized = [_validate(rule) for rule in rules]
    missing = [rule for rule in normalized if not rule_exists(rule.name)]
    if not missing:
        return {"created": [], "alreadyPresent": [r.name for r in normalized], "uacPrompted": False}
    if not _windows():
        raise FirewallError("Automatic firewall configuration is only available on Windows.")

    commands = [
        f'netsh advfirewall firewall add rule name="{r.name}" dir=in action=allow protocol={r.protocol} localport={r.port} profile=any enable=yes'
        for r in missing
    ]
    prompted = not is_elevated()
    if prompted:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False, encoding="utf-8-sig") as f:
            f.write("$ErrorActionPreference = 'Stop'\n")
            for command in commands:
                escaped = command.replace("'", "''")
                f.write(f"cmd.exe /c '{escaped}'\nif ($LASTEXITCODE -ne 0) {{ exit $LASTEXITCODE }}\n")
            script_path = f.name
        try:
            escaped_path = script_path.replace("'", "''")
            ps = f"$p=Start-Process powershell.exe -Verb RunAs -Wait -PassThru -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"{escaped_path}\"'; exit $p.ExitCode"
            result = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], capture_output=True, text=True, timeout=180, **hidden_process_kwargs())
        finally:
            Path(script_path).unlink(missing_ok=True)
    else:
        result = subprocess.run(["cmd", "/c", " && ".join(commands)], capture_output=True, text=True, timeout=120, **hidden_process_kwargs())

    if result.returncode != 0:
        raise FirewallError("Windows did not add the firewall rules. Approve the UAC prompt with 'Yes' and try again.")
    failed = [r.name for r in missing if not rule_exists(r.name)]
    if failed:
        raise FirewallError("Windows reported success, but these rules are missing: " + ", ".join(failed))
    logger.info("firewall: created %s", ", ".join(r.name for r in missing))
    return {"created": [r.name for r in missing], "alreadyPresent": [r.name for r in normalized if r not in missing], "uacPrompted": prompted}


def add_inbound_rule(rule_name: str, port: int, protocol: str = "TCP") -> None:
    ensure_inbound_rules([FirewallRule(rule_name, port, protocol)])


def instance_rules(instance: dict, *, include_rest: bool = True) -> list[FirewallRule]:
    safe_name = str(instance.get("name") or instance.get("id") or "Server").replace('"', "'")
    prefix = f"ExilesGameManager - {safe_name}"
    game_port = int(instance.get("gamePort") or 8211)
    rules = [FirewallRule(f"{prefix} - Game UDP {game_port}", game_port, "UDP")]
    if bool(instance.get("useQueryPort")) and instance.get("queryPort"):
        query = int(instance["queryPort"])
        rules.append(FirewallRule(f"{prefix} - Query UDP {query}", query, "UDP"))
    if include_rest and instance.get("rconPort"):
        rest = int(instance["rconPort"])
        rules.append(FirewallRule(f"{prefix} - REST API TCP {rest}", rest, "TCP"))
    return rules


def sync_instance(instance: dict) -> dict[str, object]:
    return ensure_inbound_rules(instance_rules(instance))


def delete_rules(rule_names: list[str]) -> dict[str, object]:
    names = [name for name in dict.fromkeys(rule_names) if name]
    existing = [name for name in names if rule_exists(name)]
    if not existing:
        return {"removed": [], "uacPrompted": False}
    if not _windows():
        raise FirewallError("Automatic firewall configuration is only available on Windows.")
    commands = [f'netsh advfirewall firewall delete rule name="{name.replace(chr(34), chr(39))}"' for name in existing]
    prompted = not is_elevated()
    if prompted:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False, encoding="utf-8-sig") as f:
            f.write("$ErrorActionPreference = 'Stop'\n")
            for command in commands:
                escaped = command.replace("'", "''")
                f.write(f"cmd.exe /c '{escaped}'\nif ($LASTEXITCODE -ne 0) {{ exit $LASTEXITCODE }}\n")
            script_path = f.name
        try:
            escaped_path = script_path.replace("'", "''")
            ps = f"$p=Start-Process powershell.exe -Verb RunAs -Wait -PassThru -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"{escaped_path}\"'; exit $p.ExitCode"
            result = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], capture_output=True, text=True, timeout=180, **hidden_process_kwargs())
        finally:
            Path(script_path).unlink(missing_ok=True)
    else:
        result = subprocess.run(["cmd", "/c", " && ".join(commands)], capture_output=True, text=True, timeout=120, **hidden_process_kwargs())
    if result.returncode != 0:
        raise FirewallError("Windows did not remove the firewall rules.")
    return {"removed": existing, "uacPrompted": prompted}


def instance_status(instance: dict) -> dict[str, object]:
    rules = instance_rules(instance)
    rows = [{"name": r.name, "port": r.port, "protocol": r.protocol, "exists": rule_exists(r.name)} for r in rules]
    return {"instanceId": instance["id"], "instanceName": instance["name"], "healthy": all(r["exists"] for r in rows), "rules": rows}
