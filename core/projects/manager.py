"""Persistencia de proyectos independientes de Creador Personalizado.

Cada proyecto vive en su propia carpeta y conserva su configuración y recursos.
No depende de Qt para poder probarse de forma aislada.
"""
from __future__ import annotations

import copy
import json
import os
import re
import shutil
import tempfile
import time
import uuid
from pathlib import Path

SCHEMA_VERSION = 1
ASSET_FIELDS = ("plymouth_image", "installer_banner", "app_path", "app2_path")
SECRET_FIELDS = {"password", "desktop_password", "ssh_password", "token", "secret"}


def _slug(value: str) -> str:
    value = re.sub(r"[^\w.-]+", "-", str(value or "").strip(), flags=re.UNICODE)
    value = value.strip(".-_")[:64]
    return value or "proyecto"


def _safe_config(config: dict) -> dict:
    result = copy.deepcopy(config or {})
    for key in list(result):
        lowered = key.lower()
        if lowered in SECRET_FIELDS or lowered.endswith("_secret") or lowered.endswith("_token"):
            result.pop(key, None)
    return result


class ProjectStore:
    """CRUD atómico para proyectos locales, con recursos autocontenidos."""

    def __init__(self, root=None):
        self.root = Path(root or (Path.home() / ".local" / "share" / "creador-personalizado" / "projects")).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, name: str, project_type: str, config: dict) -> dict:
        name = str(name or "").strip()
        project_type = str(project_type or "custom").strip().lower()
        if not name:
            raise ValueError("El nombre del proyecto no puede estar vacío")
        project_id = str(uuid.uuid4())
        base = self.root / f"{_slug(name)}-{project_id[:8]}"
        base.mkdir(parents=True, exist_ok=False)
        (base / "assets").mkdir()
        (base / "builds").mkdir()
        (base / "logs").mkdir()
        record = {
            "schema_version": SCHEMA_VERSION,
            "id": project_id,
            "name": name,
            "project_type": project_type,
            "profile_id": str((config or {}).get("profile_id") or ""),
            "profile_name": str((config or {}).get("profile_name") or ""),
            "engine": "kiosk" if project_type == "kiosk" else "desktop",
            "created_at": time.time(),
            "updated_at": time.time(),
            "config": _safe_config(config),
        }
        self._write(base, record)
        self.save(base, record["config"])
        return self.load(base)

    def save(self, project_path, config: dict) -> dict:
        base = Path(project_path).expanduser().resolve()
        current = self._read(base)
        safe = _safe_config(config)
        assets = base / "assets"
        assets.mkdir(parents=True, exist_ok=True)
        for key in ASSET_FIELDS:
            source_value = safe.get(key)
            if not source_value:
                continue
            source = Path(str(source_value)).expanduser()
            if not source.exists():
                # Mantiene una referencia relativa ya guardada, si existe.
                continue
            try:
                source_resolved = source.resolve()
                if source_resolved == base or base in source_resolved.parents:
                    safe[key] = source_resolved.relative_to(base).as_posix()
                    continue
            except OSError:
                continue
            target_dir = assets / key
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / source.name
            if source.is_dir():
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(source, target, symlinks=False)
            elif source.is_file():
                shutil.copy2(source, target)
            else:
                continue
            safe[key] = target.relative_to(base).as_posix()
        output_dir = safe.get("output_dir")
        if output_dir:
            output_path = Path(str(output_dir)).expanduser()
            try:
                resolved_output = output_path.resolve()
                if resolved_output == base or base in resolved_output.parents:
                    safe["output_dir"] = resolved_output.relative_to(base).as_posix()
            except OSError:
                pass
        current["config"] = safe
        current["project_type"] = str(safe.get("project_type") or current.get("project_type") or "custom")
        current["profile_id"] = str(safe.get("profile_id") or current.get("profile_id") or "")
        current["profile_name"] = str(safe.get("profile_name") or current.get("profile_name") or "")
        current["engine"] = str(safe.get("engine") or ("kiosk" if current["project_type"] == "kiosk" else "desktop"))
        current["updated_at"] = time.time()
        self._write(base, current)
        return self.load(base)

    def load(self, project_path) -> dict:
        base = Path(project_path).expanduser().resolve()
        record = self._read(base)
        config = copy.deepcopy(record.get("config") or {})
        for key in (*ASSET_FIELDS, "output_dir"):
            value = config.get(key)
            if value:
                path = Path(str(value))
                if not path.is_absolute():
                    config[key] = str((base / path).resolve())
        record["config"] = config
        record["path"] = str(base)
        return record

    def list_projects(self) -> list[dict]:
        projects = []
        for manifest in self.root.glob("*/project.json"):
            try:
                record = self._read(manifest.parent)
                projects.append({
                    "id": record["id"], "name": record["name"],
                    "project_type": record.get("project_type", "custom"),
                    "profile_id": record.get("profile_id", ""),
                    "profile_name": record.get("profile_name", ""),
                    "engine": record.get("engine", "desktop"),
                    "path": str(manifest.parent),
                    "updated_at": record.get("updated_at", 0),
                })
            except (OSError, ValueError, KeyError, json.JSONDecodeError):
                continue
        return sorted(projects, key=lambda item: item["updated_at"], reverse=True)

    def _read(self, base: Path) -> dict:
        manifest = base / "project.json"
        if not manifest.is_file():
            raise FileNotFoundError(f"No se encontró project.json en {base}")
        record = json.loads(manifest.read_text(encoding="utf-8"))
        if not isinstance(record, dict) or not record.get("id") or not isinstance(record.get("config"), dict):
            raise ValueError(f"Proyecto inválido: {manifest}")
        return record

    @staticmethod
    def _write(base: Path, record: dict) -> None:
        base.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=".project-", suffix=".tmp", dir=base)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(record, stream, ensure_ascii=False, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, base / "project.json")
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
