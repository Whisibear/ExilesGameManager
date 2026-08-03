"""Covers app/paths.py's migrate_data_dir(): a real dedicated server's data
can be several GB, and the old plain shutil.move() implementation could
leave documents_data_dir() half-populated if interrupted mid-copy - which
was then permanently mistaken for a completed migration, since the only
check anywhere for "has this already happened" is documents_data_dir()
existing at all. migrate_data_dir() now goes through safe_replace_dir(),
which only ever creates the destination once a verified copy is confirmed
complete.
"""

import pathlib

import pytest

from app import paths
from app.services.safe_replace import SafeReplaceError


def _make_dir(root, name, files: dict[str, bytes]) -> pathlib.Path:
    d = root / name
    d.mkdir(parents=True)
    for rel, data in files.items():
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_bytes(data)
    return d


def test_migrate_data_dir_moves_everything_and_removes_legacy(tmp_path, monkeypatch):
    legacy = _make_dir(tmp_path, "legacy", {"instances.json": b"{}", "servers/one/Level.sav": b"world"})
    documents_root = tmp_path / "Documents"
    monkeypatch.setattr(paths, "documents_data_dir", lambda: documents_root / "ExilesGameManager" / "data")

    new_dir = paths.migrate_data_dir(legacy)

    assert new_dir == documents_root / "ExilesGameManager" / "data"
    assert (new_dir / "instances.json").read_bytes() == b"{}"
    assert (new_dir / "servers" / "one" / "Level.sav").read_bytes() == b"world"
    assert not legacy.exists()


def test_migrate_data_dir_leaves_no_partial_destination_when_copy_fails(tmp_path, monkeypatch):
    legacy = _make_dir(tmp_path, "legacy", {"instances.json": b"{}"})
    documents_root = tmp_path / "Documents"
    new_dir = documents_root / "ExilesGameManager" / "data"
    monkeypatch.setattr(paths, "documents_data_dir", lambda: new_dir)

    from app.services import safe_replace

    def broken_copytree(*args, **kwargs):
        raise OSError("simulated interrupted copy")

    monkeypatch.setattr(safe_replace.shutil, "copytree", broken_copytree)

    with pytest.raises(SafeReplaceError):
        paths.migrate_data_dir(legacy)

    # The core guarantee: a failed/interrupted attempt must not leave
    # documents_data_dir() existing at all, since that's the only signal
    # the caller uses to decide "don't offer this migration again."
    assert not new_dir.exists()
    # And the original data must still be fully intact, untouched.
    assert (legacy / "instances.json").read_bytes() == b"{}"
