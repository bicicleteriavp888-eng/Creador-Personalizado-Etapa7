"""Prueba de humo BIOS/UEFI con QEMU y captura de pantalla.

La herramienta distingue evidencia serial, actividad gráfica y ausencia de
evidencia. No interpreta una VM que simplemente sigue viva como arranque OK.
"""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path

BOOT_MARKERS = ("anaconda", "dracut", "welcome to fedora", "login:", "systemd")


def _ppm_has_graphics(path: Path) -> bool:
    """Detecta una captura PPM no vacía con más de unos pocos colores."""
    try:
        data = path.read_bytes()
        if not data.startswith(b"P6"):
            return False
        # Parsear los tres campos del encabezado PPM, admitiendo comentarios.
        index = 2
        tokens = []
        while len(tokens) < 3:
            while index < len(data) and data[index] in b" \t\r\n":
                index += 1
            if index < len(data) and data[index:index + 1] == b"#":
                while index < len(data) and data[index] not in b"\r\n":
                    index += 1
                continue
            start = index
            while index < len(data) and data[index] not in b" \t\r\n":
                index += 1
            tokens.append(int(data[start:index]))
        while index < len(data) and data[index] in b" \t\r\n":
            index += 1
        width, height, maximum = tokens
        if width < 320 or height < 200 or maximum <= 0:
            return False
        pixels = data[index:]
        if len(pixels) < width * height * 3:
            return False
        sample = pixels[::max(3, (len(pixels) // 50000 // 3) * 3)]
        return len(set(sample[:50000])) > 8 and any(sample)
    except (OSError, ValueError, IndexError):
        return False


def _capture_screen(monitor_path: Path, screenshot: Path) -> bool:
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(3)
            client.connect(str(monitor_path))
            try:
                client.recv(4096)
            except OSError:
                pass
            client.sendall(f"screendump {screenshot}\n".encode())
            time.sleep(1)
            try:
                client.recv(4096)
            except OSError:
                pass
        return _ppm_has_graphics(screenshot)
    except OSError:
        return False


def run_qemu_smoke(iso_path: str, firmware: str = "bios", timeout: int = 90,
                   memory_mb: int = 2048) -> dict:
    iso = Path(iso_path).expanduser().resolve()
    if not iso.is_file():
        return {"status": "INVALID_ISO", "error": f"No existe la ISO: {iso}"}
    qemu = shutil.which("qemu-system-x86_64")
    if not qemu:
        return {"status": "UNAVAILABLE", "error": "No está instalado qemu-system-x86_64."}
    command = [
        qemu, "-m", str(max(1024, int(memory_mb))), "-cdrom", str(iso),
        "-boot", "d", "-no-reboot", "-no-shutdown", "-display", "none",
        "-vga", "std", "-nic", "none",
    ]
    if firmware == "uefi":
        code = os.environ.get("OVMF_CODE", "/usr/share/edk2/ovmf/OVMF_CODE.fd")
        if not Path(code).is_file():
            return {"status": "UNAVAILABLE", "error": "No se encontró OVMF_CODE; instala edk2-ovmf."}
        command += ["-drive", f"if=pflash,format=raw,readonly=on,file={code}"]
    elif firmware != "bios":
        return {"status": "INVALID_MODE", "error": "firmware debe ser bios o uefi."}

    with tempfile.TemporaryDirectory(prefix="creador-qemu-") as tmp:
        tmp_path = Path(tmp)
        monitor = tmp_path / "monitor.sock"
        serial = tmp_path / "serial.log"
        screenshot = tmp_path / "screen.ppm"
        command += [
            "-monitor", f"unix:{monitor},server,nowait",
            "-serial", f"file:{serial}",
        ]
        process = None
        try:
            process = subprocess.Popen(
                command, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            )
            wait_seconds = max(8, min(35, int(timeout) // 2))
            deadline = time.monotonic() + wait_seconds
            while time.monotonic() < deadline and process.poll() is None:
                if monitor.exists():
                    break
                time.sleep(0.25)
            if process.poll() is not None:
                stderr = process.stderr.read().decode("utf-8", "replace") if process.stderr else ""
                return {"status": "QEMU_EXITED_EARLY", "error": stderr[-2000:],
                        "firmware": firmware, "returncode": process.returncode}
            time.sleep(min(8, max(2, wait_seconds // 4)))
            display = _capture_screen(monitor, screenshot)
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
            serial_text = serial.read_text(errors="replace") if serial.exists() else ""
            markers = [marker for marker in BOOT_MARKERS if marker in serial_text.lower()]
            if markers:
                status = "BOOT_MARKER_FOUND"
            elif display:
                status = "DISPLAY_ACTIVITY_DETECTED"
            else:
                status = "NO_BOOT_EVIDENCE"
            return {
                "status": status, "firmware": firmware, "markers": markers,
                "display_activity": display, "serial_tail": serial_text[-4000:],
                "command": command,
                "note": (
                    "BOOT_MARKER_FOUND requiere texto serial reconocible; "
                    "DISPLAY_ACTIVITY_DETECTED solo confirma actividad de vídeo, "
                    "no que el escritorio o Anaconda hayan completado el arranque."
                ),
            }
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"status": "QEMU_ERROR", "firmware": firmware, "error": str(exc)}
        finally:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait()
