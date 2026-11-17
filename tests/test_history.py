import json
from pathlib import Path

import pytest

from core.history import BackupManager, BuildHistory, redact_config


def test_redaction_is_recursive():
    value = redact_config({"password": "abc", "nested": {"ssh_token": "xyz", "ok": 2}})
    assert value["password"] == "[REDACTED]"
    assert value["nested"]["ssh_token"] == "[REDACTED]"
    assert value["nested"]["ok"] == 2


def test_history_lifecycle_and_hash(tmp_path):
    iso = tmp_path / "demo.iso"
    iso.write_bytes(b"iso-fixture")
    history = BuildHistory(tmp_path / "history.sqlite3")
    build_id = history.start({"iso_name": "Demo", "password": "should-not-persist"})
    history.finish(build_id, "GENERATED", iso)
    row = history.get(build_id)
    assert row["status"] == "GENERATED"
    assert row["iso_sha256"]
    assert "should-not-persist" not in row["config_json"]
    assert history.list()[0]["build_id"] == build_id


def test_backup_verify_restore_and_tamper(tmp_path):
    source = tmp_path / "project"
    source.mkdir()
    (source / "README.md").write_text("hello", encoding="utf-8")
    (source / "nested").mkdir()
    (source / "nested" / "data.txt").write_text("world", encoding="utf-8")
    manager = BackupManager(tmp_path / "backups")
    result = manager.create(source, "test")
    assert result["files"] == 2
    assert manager.verify(result["path"])["valid"]
    restored = tmp_path / "restored"
    manager.restore(result["path"], restored)
    assert (restored / "README.md").read_text() == "hello"
    assert (restored / "nested" / "data.txt").read_text() == "world"
    with pytest.raises(FileExistsError):
        manager.restore(result["path"], restored)


def test_backup_rejects_traversal(tmp_path):
    import tarfile
    archive = tmp_path / "bad.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        import io
        data = b"bad"
        info = tarfile.TarInfo("../escape")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    manager = BackupManager(tmp_path / "backups")
    with pytest.raises(ValueError):
        manager.verify(archive)
