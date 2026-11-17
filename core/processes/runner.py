"""Ejecucion controlada de procesos externos."""

import os
import signal
import subprocess


def run_command(cmd):
    """Ejecuta un comando sin entrada interactiva y captura su salida."""
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )


def must(result, action):
    """Lanza RuntimeError con el detalle real si el comando fallo."""
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(
            f"No pude {action}: {detail or 'codigo ' + str(result.returncode)}"
        )
    return result


def signal_process_group(process, sig):
    """Manda una senal al grupo completo; si falla, solo al proceso."""
    try:
        os.killpg(os.getpgid(process.pid), sig)
        return
    except (ProcessLookupError, PermissionError, OSError):
        pass
    try:
        process.send_signal(sig)
    except (ProcessLookupError, PermissionError, OSError):
        pass


def terminate_process_tree(process, timeout=10):
    """SIGTERM al arbol completo y SIGKILL si no alcanza en ``timeout``."""
    signal_process_group(process, signal.SIGTERM)
    try:
        process.wait(timeout=timeout)
        return
    except subprocess.TimeoutExpired:
        pass
    signal_process_group(process, signal.SIGKILL)
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        pass
