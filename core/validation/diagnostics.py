"""Diagnostico del host previo a la compilacion."""

import os
import shutil
import subprocess

from core.constants import MIN_FREE_BYTES

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
RPM_HELPERS = (
    ("rpm", "rpm"),
    ("createrepo_c", "createrepo_c"),
)
SERVICE_NAMES = ("firewalld", "sshd")

INSTALL_HINT = (
    "Instala las dependencias con: sudo dnf install "
    "livecd-tools openssl lorax xorriso syslinux"
)


def check_dependencies(extra_binaries=()):
    """Devuelve el estado real de las herramientas y activos del build.

    ``extra_binaries`` permite sumar dependencias condicionales (por ejemplo
    ``rpm`` y ``createrepo_c`` cuando se usa un RPM local).
    """
    tools = []
    missing = []
    for binary, package in REQUIRED_BINARIES:
        path = shutil.which(binary)
        tools.append({"name": binary, "path": path or "", "package": package})
        if not path:
            missing.append({"name": binary, "package": package})

    for binary, package in extra_binaries:
        path = shutil.which(binary)
        tools.append({"name": binary, "path": path or "", "package": package})
        if not path:
            missing.append({"name": binary, "package": package})

    assets = []
    for path, package in REQUIRED_SYSlinux:
        exists = os.path.isfile(path)
        assets.append(
            {
                "name": os.path.basename(path),
                "path": path if exists else "",
                "package": package,
            }
        )
        if not exists:
            missing.append({"name": os.path.basename(path), "package": package})

    total = len(tools) + len(assets)
    return {
        "ok": not missing,
        "tools": tools,
        "assets": assets,
        "missing": missing,
        "total": total,
        "available": total - len(missing),
    }


def preflight(uses_local_rpm=False):
    """Verifica el host y lanza RuntimeError con todos los faltantes juntos."""
    extras = RPM_HELPERS if uses_local_rpm else ()
    status = check_dependencies(extras)
    if status["ok"]:
        return status

    names = {item["name"] for item in status["missing"]}
    missing = [
        name
        for name, _package in REQUIRED_BINARIES + tuple(extras)
        if name in names
    ]
    missing_assets = [
        path
        for path, _package in REQUIRED_SYSlinux
        if os.path.basename(path) in names
    ]
    rpm_helpers = (
        [name for name, _package in RPM_HELPERS if name in names]
        if uses_local_rpm
        else []
    )

    problems = []
    if missing:
        problems.append("faltan herramientas: {}".format(", ".join(missing)))
    if missing_assets:
        problems.append(
            "faltan archivos de syslinux: {}".format(", ".join(missing_assets))
        )
    if rpm_helpers:
        problems.append(
            "faltan herramientas para RPM locales: {}".format(
                ", ".join(rpm_helpers)
            )
        )

    hint = INSTALL_HINT + (" createrepo_c" if rpm_helpers else "")
    raise RuntimeError(
        "El host no esta listo para compilar: "
        + "; ".join(problems)
        + ". "
        + hint
    )


def disk_info(path, min_free=MIN_FREE_BYTES):
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
        "ok": usage.free >= min_free,
        "path": candidate,
        "total": usage.total,
        "used": usage.used,
        "free": usage.free,
        "enough": usage.free >= min_free,
    }


def check_disk(path, min_free=MIN_FREE_BYTES):
    """Valida espacio y descarta directorios de trabajo sobre tmpfs."""
    free = shutil.disk_usage(path).free
    if free < min_free:
        raise RuntimeError(
            "Espacio insuficiente en {}: {:.1f} GiB libres; se requieren "
            "al menos 12 GiB para iniciar la compilacion.".format(
                path, free / 1024 ** 3
            )
        )

    try:
        result = subprocess.run(
            ["findmnt", "-n", "-o", "FSTYPE", "-T", path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        fstype = result.stdout.strip()
    except Exception:  # noqa: BLE001
        fstype = ""

    if fstype == "tmpfs":
        raise RuntimeError(
            "El directorio de trabajo esta en tmpfs (RAM). Define "
            "KIOSK_BUILD_ROOT en un sistema de archivos respaldado por disco."
        )


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
