"""Historial persistente de compilaciones y respaldos verificables.

El módulo no depende de Qt y puede utilizarse desde la GUI o desde CLI.
Nunca persiste contraseñas ni secretos de configuración.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import tarfile
import tempfile
import time
import uuid
from pathlib import Path, PurePosixPath

_SECRET_PARTS = ("password", "passwd", "secret", "token", "private_key", "credential")


def redact_config(value):
    """Devuelve una copia JSON-safe con claves sensibles redactadas."""
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if any(part in str(key).lower() for part in _SECRET_PARTS):
                result[str(key)] = "[REDACTED]"
            else:
                result[str(key)] = redact_config(item)
        return result
    if isinstance(value, (list, tuple)):
        return [redact_config(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class BuildHistory:
    """Registro SQLite de builds, con rutas, estado, configuración y hashes."""
    def __init__(self, database=None):
        default = Path.home() / ".local" / "share" / "creador-kiosk" / "history.sqlite3"
        self.database = Path(database or default).expanduser().resolve()
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS builds (
                build_id TEXT PRIMARY KEY, started_at REAL NOT NULL,
                finished_at REAL, status TEXT NOT NULL, iso_path TEXT,
                iso_sha256 TEXT, log_path TEXT, config_json TEXT NOT NULL,
                error TEXT)""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_builds_started ON builds(started_at DESC)")

    def _connect(self):
        db = sqlite3.connect(str(self.database), timeout=15)
        db.row_factory = sqlite3.Row
        return db

    def start(self, config, log_path=None, build_id=None):
        build_id = build_id or str(uuid.uuid4())
        with self._connect() as db:
            db.execute("INSERT INTO builds(build_id,started_at,status,log_path,config_json) VALUES(?,?,?,?,?)",
                       (build_id, time.time(), "RUNNING", str(log_path or ""),
                        json.dumps(redact_config(config), ensure_ascii=False, sort_keys=True)))
        return build_id

    def finish(self, build_id, status, iso_path=None, error=None):
        allowed = {"GENERATED", "FAILED", "CANCELLED", "VALIDATED", "TESTED"}
        if status not in allowed:
            raise ValueError(f"Estado de build no permitido: {status}")
        iso_path = str(Path(iso_path).expanduser().resolve()) if iso_path else None
        digest = sha256_file(iso_path) if iso_path and os.path.isfile(iso_path) else None
        with self._connect() as db:
            cur = db.execute("UPDATE builds SET finished_at=?,status=?,iso_path=?,iso_sha256=?,error=? WHERE build_id=?",
                             (time.time(), status, iso_path, digest, str(error or "")[:4000], build_id))
            if cur.rowcount != 1:
                raise KeyError(f"Build desconocido: {build_id}")

    def list(self, limit=100):
        limit = max(1, min(int(limit), 1000))
        with self._connect() as db:
            return [dict(row) for row in db.execute(
                "SELECT * FROM builds ORDER BY started_at DESC LIMIT ?", (limit,))]

    def get(self, build_id):
        with self._connect() as db:
            row = db.execute("SELECT * FROM builds WHERE build_id=?", (build_id,)).fetchone()
            return dict(row) if row else None


class BackupManager:
    """Crea snapshots tar.gz con manifiesto SHA-256 y restaura sin traversal."""
    EXCLUDED = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "backups"}

    def __init__(self, backup_dir):
        self.backup_dir = Path(backup_dir).expanduser().resolve()
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create(self, source_dir, label="manual"):
        source = Path(source_dir).expanduser().resolve()
        if not source.is_dir():
            raise ValueError("El origen del respaldo no es un directorio")
        stamp = time.strftime("%Y%m%d-%H%M%S")
        safe_label = "".join(c if c.isalnum() or c in "-_" else "-" for c in label)[:40] or "manual"
        target = self.backup_dir / f"{stamp}-{safe_label}.tar.gz"
        files = []
        with tempfile.TemporaryDirectory(prefix="ck-backup-") as temp:
            manifest_path = Path(temp) / "MANIFEST.sha256"
            with tarfile.open(target, "w:gz") as archive:
                for path in sorted(source.rglob("*")):
                    if not path.is_file() or path.is_symlink() or any(part in self.EXCLUDED for part in path.relative_to(source).parts):
                        continue
                    try:
                        path.relative_to(self.backup_dir)
                        continue  # nunca incluir el propio directorio de respaldos
                    except ValueError:
                        pass
                    rel = path.relative_to(source).as_posix()
                    if rel.startswith("../") or path.is_symlink():
                        continue
                    digest = sha256_file(path)
                    files.append((rel, digest))
                    archive.add(path, arcname=f"project/{rel}", recursive=False)
                manifest_path.write_text("".join(f"{digest}  {name}\n" for name, digest in files), encoding="utf-8")
                archive.add(manifest_path, arcname="MANIFEST.sha256")
        return {"path": str(target), "sha256": sha256_file(target), "files": len(files)}

    def verify(self, archive_path):
        archive_path = Path(archive_path).expanduser().resolve()
        with tarfile.open(archive_path, "r:gz") as archive:
            members = archive.getmembers()
            names = [m.name for m in members]
            if len(names) != len(set(names)):
                raise ValueError("El respaldo contiene rutas duplicadas")
            if "MANIFEST.sha256" not in names:
                raise ValueError("El respaldo no contiene manifiesto")
            for member in members:
                p = PurePosixPath(member.name)
                if p.is_absolute() or ".." in p.parts or not member.isfile():
                    raise ValueError(f"Tipo o ruta insegura dentro del respaldo: {member.name}")
            manifest = archive.extractfile("MANIFEST.sha256").read().decode("utf-8")
            expected = {}
            for line in manifest.splitlines():
                digest, name = line.split("  ", 1)
                expected[name] = digest
            actual_names = {n.removeprefix("project/") for n in names if n.startswith("project/") and not n.endswith("/")}
            if actual_names != set(expected):
                raise ValueError("El contenido del respaldo no coincide con el manifiesto")
            for name, digest in expected.items():
                stream = archive.extractfile("project/" + name)
                actual = hashlib.sha256(stream.read()).hexdigest()
                if actual != digest:
                    raise ValueError(f"Hash incorrecto: {name}")
        return {"valid": True, "files": len(expected), "sha256": sha256_file(archive_path)}

    def restore(self, archive_path, destination):
        destination = Path(destination).expanduser().resolve()
        if destination.exists() and any(destination.iterdir()):
            raise FileExistsError("El destino debe estar vacío para evitar sobrescribir datos")
        self.verify(archive_path)
        destination.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive_path, "r:gz") as archive:
            for member in archive.getmembers():
                if member.name.startswith("project/"):
                    member.name = member.name[len("project/"):]
                    archive.extract(member, destination, filter="data")
        return str(destination)
