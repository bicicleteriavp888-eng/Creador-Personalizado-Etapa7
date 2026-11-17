"""Deteccion del prefijo de privilegios para tareas que necesitan root."""

import os
import shutil
import subprocess


def detect_privilege_prefix(emit=None):
    """Devuelve el prefijo para ejecutar un comando como root sin colgarse.

    Intenta ``sudo -n`` (sin password) y, si no esta disponible, usa
    ``pkexec --keep-cwd`` para que el dialogo de polkit aparezca en la sesion
    grafica. ``emit`` es un callback opcional para informar en la GUI.
    """
    if os.geteuid() == 0:
        return []

    sudo = shutil.which("sudo")
    if sudo:
        probe = subprocess.run(
            [sudo, "-n", "true"],
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
        )
        if probe.returncode == 0:
            if emit:
                emit("🔐 Autorización administrativa disponible mediante sudo -n.")
            return [sudo, "-n"]

    pkexec = shutil.which("pkexec")
    gui_session = bool(
        os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY")
    )
    if pkexec and gui_session:
        if emit:
            emit(
                "🔐 sudo sin contrasena no disponible: se usara pkexec "
                "(polkit pedira autorizacion en un dialogo)."
            )
        # Sin --keep-cwd, pkexec ejecuta el programa en /root y livecd-creator
        # dejaria la ISO alli en lugar del directorio de trabajo.
        return [pkexec, "--keep-cwd"]

    raise RuntimeError(
        "No hay forma de obtener privilegios de forma no interactiva. "
        "Ejecuta 'sudo -v' en una terminal y reintenta, o agrega una regla "
        "NOPASSWD en /etc/sudoers.d/."
    )
