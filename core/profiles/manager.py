"""Gestión segura de perfiles versionados de Creador-kiosk."""
import json
import os
import re
import tempfile
from pathlib import Path

_PROJECT_PROFILES = Path(__file__).resolve().parents[2] / "profiles"
_SYSTEM_PROFILES = Path("/usr/share/creador-kiosk/profiles")
PROFILES_DIR = _PROJECT_PROFILES if _PROJECT_PROFILES.is_dir() else _SYSTEM_PROFILES
PROFILE_KEY = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def _path(profile_key, directory=None):
    key = str(profile_key or "")
    if not PROFILE_KEY.fullmatch(key) or key == "schema":
        raise ValueError("Identificador de perfil inválido")
    root = Path(directory or PROFILES_DIR).resolve()
    path = (root / f"{key}.json").resolve()
    if path.parent != root:
        raise ValueError("Ruta de perfil fuera del directorio permitido")
    return path


def list_available_profiles(directory=None):
    root = Path(directory or PROFILES_DIR)
    if not root.exists():
        return []
    return sorted(p.stem for p in root.glob("*.json") if p.name != "schema.json" and PROFILE_KEY.fullmatch(p.stem))


def load_profile(profile_key, directory=None):
    path = _path(profile_key, directory)
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("El perfil debe ser un objeto JSON")
    return data


def save_profile(profile_key, profile_data, directory=None):
    if not isinstance(profile_data, dict):
        raise ValueError("Los datos del perfil deben ser un objeto")
    path = _path(profile_key, directory)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(profile_data)
    payload.setdefault("schema_version", 1)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return str(path)


def export_profile(profile_key, destination, directory=None):
    data = load_profile(profile_key, directory)
    if data is None:
        raise FileNotFoundError(profile_key)
    target = Path(destination).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return str(target)


def import_profile(source, profile_key, directory=None):
    data = json.loads(Path(source).expanduser().read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("El perfil importado debe ser un objeto JSON")
    return save_profile(profile_key, data, directory)


def delete_profile(profile_key, directory=None):
    path = _path(profile_key, directory)
    if profile_key in ("kiosco-navegador", "kiosco-multiventana"):
        return False
    if path.is_file():
        path.unlink()
        return True
    return False
