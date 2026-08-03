import json
import zipfile
from pathlib import Path

from app.services import diagnostics, runtime_logging


def test_http_audit_writes_jsonl(data_dir: Path):
    runtime_logging.write_http_event({"type": "http", "method": "GET", "path": "/api/health", "status": 200})
    path = runtime_logging.http_audit_path()
    row = json.loads(path.read_text(encoding="utf-8").splitlines()[-1])
    assert row["path"] == "/api/health"
    assert row["status"] == 200
    assert "timestamp" in row


def test_diagnostic_package_is_created_and_excludes_raw_secrets(data_dir: Path):
    runtime_logging.logs_root()
    secret_log = runtime_logging.logs_root() / "backend" / "secret.log"
    secret_log.write_text("password=not-for-support token=private-value", encoding="utf-8")
    result = diagnostics.create_package()
    package = diagnostics.package_path(result["fileName"])
    assert package.is_file()
    with zipfile.ZipFile(package) as archive:
        text = "\n".join(
            archive.read(name).decode("utf-8", errors="replace")
            for name in archive.namelist()
            if name.endswith((".log", ".txt", ".json", ".jsonl"))
        )
    assert "not-for-support" not in text
    assert "private-value" not in text
    assert "***REDACTED***" in text
