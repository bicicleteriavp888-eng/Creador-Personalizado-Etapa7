"""Gestión conservadora de la caché persistente de livecd-creator."""
from __future__ import annotations
import os
import shutil
from pathlib import Path

DEFAULT_CACHE_DIR = "/var/cache/creador-personalizado"


def cache_info(path: str | None = None) -> dict:
    target = Path(path or os.environ.get("CREADOR_CACHE_DIR") or os.environ.get("KIOSK_CACHE_DIR") or DEFAULT_CACHE_DIR).expanduser()
    try:
        size = sum(p.stat().st_size for p in target.rglob("*") if p.is_file()) if target.exists() else 0
        return {"path": str(target), "exists": target.exists(), "size_bytes": size}
    except OSError as exc:
        return {"path": str(target), "exists": target.exists(), "size_bytes": 0, "error": str(exc)}


def clear_cache(path: str | None = None, *, confirm: bool = False) -> dict:
    """Vacía solo el directorio de caché conocido; nunca acepta rutas raíz."""
    if not confirm:
        raise PermissionError("Se requiere confirmación explícita para borrar la caché.")
    target = Path(path or os.environ.get("CREADOR_CACHE_DIR") or os.environ.get("KIOSK_CACHE_DIR") or DEFAULT_CACHE_DIR).expanduser().resolve()
    allowed_roots = {Path("/var/cache/creador-personalizado").resolve(), Path("/var/cache/creador-kiosk").resolve()}
    if target not in allowed_roots:
        raise ValueError("Por seguridad solo se puede limpiar la caché estándar de Creador-Personalizado.")
    if target.exists():
        for child in target.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
    return cache_info(str(target))
