"""Consultas reales del sistema para el panel principal."""

import hashlib
import os
import shutil
import sqlite3
import subprocess
import threading
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.builder import MIN_FREE_BYTES

REQUIRED_BINARIES = (
    ("livecd-creator", "livecd-tools"),
    ("openssl", "openssl"),
    ("mkefiboot", "lorax"),
    ("xorrisofs", "xorriso"),
)
REQUIRED_SYSlinux = (
    ("/usr/share/syslinux/isolinux.bin", "syslinux"),
    ("/usr/share/syslinux/isohdpfx.bin", "syslinux"),
    ("/usr/share/syslinux/vesamenu.c32", "syslinux"),
)
SERVICE_NAMES = ("firewalld", "sshd")


def check_dependencies():
    """Devuelve el estado real de las herramientas y activos del build."""
    tools = []
    missing = []
    for binary, package in REQUIRED_BINARIES:
        path = shutil.which(binary)
        tools.append({"name": binary, "path": path or "", "package": package})
        if not path:
            missing.append({"name": binary, "package": package})

    assets = []
    for path, package in REQUIRED_SYSlinux:
        exists = os.path.isfile(path)
        assets.append({"name": os.path.basename(path), "path": path if exists else "", "package": package})
        if not exists:
            missing.append({"name": os.path.basename(path), "package": package})

    return {
        "ok": not missing,
        "tools": tools,
        "assets": assets,
        "missing": missing,
        "total": len(tools) + len(assets),
        "available": len(tools) + len(assets) - len(missing),
    }


def disk_info(path):
    """Uso real del sistema de archivos que contiene ``path``."""
    candidate = os.path.abspath(os.path.expanduser(path or "~"))
    while not os.path.exists(candidate):
        parent = os.path.dirname(candidate)
        if parent == candidate:
            break
        candidate = parent
    try:
        usage = shutil.disk_usage(candidate)
    except OSError as exc:
        return {"ok": False, "path": candidate, "error": str(exc)}
    return {
        "ok": usage.free >= MIN_FREE_BYTES,
        "path": candidate,
        "total": usage.total,
        "used": usage.used,
        "free": usage.free,
        "enough": usage.free >= MIN_FREE_BYTES,
    }


def service_states(names=SERVICE_NAMES):
    """Estado real de los servicios consultados con systemctl."""
    states = {}
    for name in names:
        try:
            result = subprocess.run(
                ["systemctl", "is-active", name],
                capture_output=True,
                text=True,
                timeout=4,
            )
            states[name] = (result.stdout or result.stderr or "unknown").strip()
        except Exception:  # noqa: BLE001 - se muestra como no disponible
            states[name] = "no disponible"
    return states


class HostStatusWorker(QThread):
    """Consulta los servicios del host sin bloquear el hilo de la interfaz.

    ``systemctl is-active`` puede tardar varios segundos si el host esta bajo
    carga; por eso el panel y el paso de seguridad lo consultan en segundo
    plano. El resultado siempre es el estado real, nunca un valor inventado.
    """

    ready = Signal(dict)

    def __init__(self, names=SERVICE_NAMES):
        super().__init__()
        self.names = tuple(names)

    def run(self):
        try:
            states = service_states(self.names)
        except Exception:  # noqa: BLE001 - el hilo debe informar, no morir
            states = {name: "no disponible" for name in self.names}
        self.ready.emit(states)


def recent_builds(limit=4, database=None):
    """Lee las ultimas compilaciones del historial SQLite real.

    No crea la base si no existe: un panel vacio es preferible a inventar
    actividad. Devuelve una lista de diccionarios (posiblemente vacia).
    """
    path = Path(
        database
        or os.path.expanduser("~/.local/share/creador-kiosk/history.sqlite3")
    ).expanduser()
    if not path.is_file():
        return []
    try:
        uri = path.resolve().as_uri() + "?mode=ro"
        connection = sqlite3.connect(uri, uri=True, timeout=2)
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(
                "SELECT build_id, started_at, finished_at, status, iso_path, "
                "error FROM builds ORDER BY started_at DESC LIMIT ?",
                (max(1, min(int(limit), 20)),),
            ).fetchall()
        finally:
            connection.close()
    except (sqlite3.Error, OSError, ValueError):
        return []
    return [dict(row) for row in rows]


def format_timestamp(value):
    """Formatea una fecha ISO o un epoch para mostrarla en el panel."""
    if not value:
        return ""
    try:
        if isinstance(value, (int, float)):
            moment = datetime.fromtimestamp(value)
        elif str(value).isdigit():
            moment = datetime.fromtimestamp(int(value))
        else:
            moment = datetime.fromisoformat(str(value))
    except (ValueError, OSError, OverflowError):
        return str(value)
    return moment.strftime("%d/%m/%Y %H:%M")


def hash_file(path, cancel_event=None, chunk_size=4 * 1024 * 1024):
    """Calcula SHA-256 por bloques; ``cancel_event`` permite abortar."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            if cancel_event is not None and cancel_event.is_set():
                return None
            block = handle.read(chunk_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


class HashWorker(QThread):
    """Calcula el SHA-256 de una ISO sin bloquear la interfaz."""

    done = Signal(str, str, int, int)
    failed = Signal(str, str)

    def __init__(self, path, size, mtime):
        super().__init__()
        self.path = path
        self.size = size
        self.mtime = mtime
        self.cancel_event = threading.Event()

    def run(self):
        try:
            digest = hash_file(self.path, self.cancel_event)
        except Exception as exc:  # noqa: BLE001 - se informa en la GUI
            self.failed.emit(self.path, str(exc))
            return
        if digest:
            self.done.emit(self.path, digest, self.size, self.mtime)

    def cancel(self):
        self.cancel_event.set()
