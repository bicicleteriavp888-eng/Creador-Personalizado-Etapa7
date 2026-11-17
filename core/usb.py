"""Enumeracion de discos USB y escritura de ISOs con dd."""

import json
import os
import re
import select
import shlex
import shutil
import stat
import subprocess

from PySide6.QtCore import QThread, Signal

from core.privileges import detect_privilege_prefix

# Puntos de montaje que nunca deben pertenecer al dispositivo de destino.
SYSTEM_MOUNTS = (
    "/boot",
    "/usr",
    "/var",
    "/etc",
    "/home",
    "/opt",
    "/srv",
    "/root",
)

# Codigos de salida que el script shell de escritura devuelve al fallar.
EXIT_DEVICE_MOUNTED = 3
EXIT_IDENTITY_CHANGED = 20
EXIT_SIZE_CHANGED = 21
EXIT_SERIAL_CHANGED = 22


def _is_system_mount(mount):
    if mount == "/":
        return True
    return any(
        mount == base or mount.startswith(base + "/")
        for base in SYSTEM_MOUNTS
    )


def size_gib(size):
    try:
        return float(size) / 1024 ** 3
    except (TypeError, ValueError):
        return 0.0


def _mountpoints(entry):
    value = entry.get("mountpoints")
    if isinstance(value, str):
        value = [value]
    return [m for m in (value or []) if m]



def _validate_device_snapshot(current, snapshot):
    """Comprueba que el USB actual siga siendo el que confirmo el usuario."""
    if not snapshot:
        return
    if not snapshot.get("major_minor"):
        raise RuntimeError(
            "No pude obtener la identidad MAJ:MIN del USB. "
            "Actualiza util-linux y vuelve a detectar el dispositivo."
        )
    for field in ("major_minor", "size", "serial", "model"):
        expected = snapshot.get(field)
        actual = current.get(field)
        if expected not in (None, "") and actual != expected:
            raise RuntimeError(
                f"La identidad del dispositivo cambio ({field}). "
                "Desconectalo, volve a seleccionarlo y reintenta."
            )


def list_usb_disks():
    """Lista los discos USB extraibles conectados, excluyendo el del sistema."""
    if shutil.which("lsblk") is None:
        raise RuntimeError("Falta el comando 'lsblk' (paquete util-linux).")

    result = subprocess.run(
        [
            "lsblk",
            "-J",
            "-b",
            "-o",
            "NAME,PATH,TYPE,SIZE,RM,RO,HOTPLUG,TRAN,MODEL,SERIAL,MAJ:MIN,MOUNTPOINTS",
        ],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "lsblk fallo: " + (result.stderr or result.stdout or "").strip()
        )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"No pude interpretar la salida de lsblk: {exc}") from exc

    disks = []
    for dev in data.get("blockdevices", []):
        if (dev.get("type") or "") != "disk":
            continue
        path = dev.get("path") or ("/dev/" + (dev.get("name") or ""))
        if not path.startswith("/dev/") or dev.get("ro"):
            continue

        tran = (dev.get("tran") or "").lower()
        removable = bool(dev.get("rm")) or bool(dev.get("hotplug"))
        if not removable and tran != "usb":
            continue

        children = []
        mounts = list(_mountpoints(dev))
        for child in dev.get("children") or []:
            child_mounts = _mountpoints(child)
            mounts.extend(child_mounts)
            children.append(
                {
                    "path": child.get("path")
                    or ("/dev/" + (child.get("name") or "")),
                    "mountpoints": child_mounts,
                }
            )

        # Nunca ofrecer el disco donde vive el sistema (incluido un host que
        # arranco desde un USB).
        if any(_is_system_mount(mount) for mount in mounts):
            continue

        disks.append(
            {
                "path": path,
                "size": int(dev.get("size") or 0),
                "model": (dev.get("model") or "").strip(),
                "serial": (dev.get("serial") or "").strip(),
                "major_minor": str(dev.get("maj:min") or dev.get("maj_min") or "").strip(),
                "tran": tran,
                "removable": removable,
                "mountpoints": mounts,
                "children": children,
            }
        )

    return disks


class USBWriterWorker(QThread):
    """Escribe una ISO en un dispositivo USB con dd (pide privilegios)."""

    log_signal = Signal(str)
    progress_signal = Signal(int)
    finished_signal = Signal(bool, str)

    def __init__(self, iso_path, device_path, device_snapshot=None, parent=None):
        super().__init__(parent)
        self.iso_path = iso_path
        self.device_path = device_path
        self.device_snapshot = dict(device_snapshot or {})

    def run(self):
        try:
            ok, message = self._write()
        except Exception as exc:  # noqa: BLE001 - se informa en la GUI
            self.log_signal.emit(f"💥 {exc}")
            ok, message = False, str(exc)
        self.finished_signal.emit(ok, message)

    def _build_write_script(self, iso, device, snapshot, partitions, swap_targets, iso_size):
        """Armado del script de validacion y escritura con dd.

        Separado como metodo propio para poder testear el script generado.
        """
        script = ["set -e"]
        if snapshot:
            expected_mm = str(snapshot.get("major_minor") or "")
            expected_size = str(snapshot.get("size") or "")
            expected_serial = str(snapshot.get("serial") or "")
            script.extend([
                "actual_mm=$(lsblk -dn -o MAJ:MIN -- " + shlex.quote(device) + " | tr -d '[:space:]')",
                "test \"$actual_mm\" = " + shlex.quote(expected_mm) + " || { echo \"ERROR: identidad MAJ:MIN cambiada (esperado: " + expected_mm + ", actual: $actual_mm)\"; exit " + str(EXIT_IDENTITY_CHANGED) + "; }",
                "actual_size=$(blockdev --getsize64 " + shlex.quote(device) + ")",
                "test \"$actual_size\" = " + shlex.quote(expected_size) + " || { echo \"ERROR: capacidad del USB cambiada (esperado: " + expected_size + ", actual: $actual_size)\"; exit " + str(EXIT_SIZE_CHANGED) + "; }",
            ])
            if expected_serial:
                script.append(
                    "actual_serial=$(lsblk -dn -o SERIAL -- " + shlex.quote(device) + " | tr -d '[:space:]')"
                )
                script.append(
                    "test \"$actual_serial\" = " + shlex.quote(expected_serial) + " || { echo \"ERROR: numero de serie cambiado (esperado: " + expected_serial + ", actual: $actual_serial)\"; exit " + str(EXIT_SERIAL_CHANGED) + "; }"
                )
        for target in swap_targets:
            # El destino puede tener una particion de swap inactiva; no debe
            # abortar la escritura por eso.
            script.append(f"swapoff {shlex.quote(target)} 2>/dev/null || true")
        for part in partitions:
            quoted = shlex.quote(part)
            script.append(
                f"if findmnt -S {quoted} >/dev/null 2>&1; "
                f"then umount {quoted}; fi"
            )
        for part in partitions:
            quoted = shlex.quote(part)
            script.append(
                f"if findmnt -S {quoted} >/dev/null 2>&1; "
                f'then echo "ERROR: {part} sigue montado"; exit ' + str(EXIT_DEVICE_MOUNTED) + "; fi"
            )
        script.append(
            "dd if={} of={} bs=4M conv=fsync status=progress".format(
                shlex.quote(iso), shlex.quote(device)
            )
        )
        script.append("sync")
        # Comparar los bytes escritos con la ISO antes de informar exito.
        script.append(
            "cmp -n {} {} {}".format(
                iso_size, shlex.quote(iso), shlex.quote(device)
            )
        )
        return script

    def _write(self):
        iso = os.path.abspath(self.iso_path)
        device = self.device_path

        if not os.path.isfile(iso):
            raise RuntimeError(f"No existe la ISO: {iso}")
        iso_size = os.path.getsize(iso)
        if iso_size <= 0:
            raise RuntimeError("La ISO esta vacia.")
        if not os.path.exists(device):
            raise RuntimeError(f"No existe el dispositivo {device}.")
        if not stat.S_ISBLK(os.stat(device).st_mode):
            raise RuntimeError(f"{device} no es un dispositivo de bloque.")

        # Reenumerar justo antes de escribir: no confiar en una ruta /dev/sdX
        # que pudo reasignarse despues de que el usuario selecciono el destino.
        disk = next(
            (item for item in list_usb_disks() if item["path"] == device),
            None,
        )
        if disk is None:
            raise RuntimeError(
                f"{device} no figura como disco USB extraible. "
                "Operacion abortada por seguridad."
            )
        snapshot = self.device_snapshot
        _validate_device_snapshot(disk, snapshot)
        try:
            device_stat = os.stat(device)
            actual_major_minor = f"{os.major(device_stat.st_rdev)}:{os.minor(device_stat.st_rdev)}"
        except OSError as exc:
            raise RuntimeError(f"No pude verificar el dispositivo {device}: {exc}") from exc
        if disk.get("major_minor") and disk["major_minor"] != actual_major_minor:
            raise RuntimeError(
                "La ruta del dispositivo no coincide con su identidad de bloque. "
                "Operacion cancelada."
            )
        if iso_size > disk["size"]:
            raise RuntimeError(
                "La ISO ({} GiB) es mas grande que el dispositivo ({} GiB).".format(
                    size_gib(iso_size), size_gib(disk["size"])
                )
            )

        # No permitir escribir si la ISO esta guardada en el mismo USB.
        real_iso = os.path.realpath(iso)
        for mount in disk["mountpoints"]:
            base = mount.rstrip("/")
            if base and real_iso.startswith(base + "/"):
                raise RuntimeError(
                    "La ISO esta guardada en el mismo dispositivo que se va a "
                    "borrar. Copiala a otra ubicacion primero."
                )

        partitions = [
            child["path"] for child in disk.get("children", []) if child["path"]
        ]
        swap_targets = []
        if "[SWAP]" in disk["mountpoints"]:
            swap_targets = [
                child["path"]
                for child in disk.get("children", [])
                if "[SWAP]" in child["mountpoints"]
            ] or [device]

        self.log_signal.emit(
            f"💽 Destino: {device} ({size_gib(disk['size']):.1f} GiB)"
        )
        self.log_signal.emit(f"📀 Imagen: {iso} ({size_gib(iso_size):.2f} GiB)")

        prefix = detect_privilege_prefix(self.log_signal.emit)

        script = self._build_write_script(
            iso, device, snapshot, partitions, swap_targets, iso_size
        )

        cmd = prefix + ["sh", "-c", "\n".join(script)]
        self.log_signal.emit(
            "🚀 dd if={} of={} bs=4M".format(iso, device)
        )

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
        )

        last_logged = -10
        buffer = b""
        try:
            fd = process.stdout.fileno()
            while True:
                ready, _, _ = select.select([fd], [], [], 1.0)
                if not ready:
                    if process.poll() is not None:
                        break
                    continue
                chunk = os.read(fd, 8192)
                if not chunk:
                    break
                buffer += chunk
                parts = re.split(rb"[\r\n]+", buffer)
                buffer = parts.pop()
                for raw in parts:
                    last_logged = self._handle_output(
                        raw.decode("utf-8", "replace"),
                        iso_size,
                        last_logged,
                    )
        finally:
            process.stdout.close()

        if buffer.strip():
            self._handle_output(
                buffer.decode("utf-8", "replace"), iso_size, last_logged
            )

        rc = process.wait()
        if rc != 0:
            return False, f"dd termino con codigo {rc}."

        self.progress_signal.emit(100)
        self.log_signal.emit("✅ Verificacion de lectura: los bytes escritos coinciden con la ISO.")
        return True, "USB escrito y verificado correctamente. Ya podes arrancar desde el USB."

    def _handle_output(self, text, iso_size, last_logged):
        text = text.strip()
        if not text:
            return last_logged

        match = re.match(r"^(\d+)\s+bytes\b", text)
        if match:
            copied = int(match.group(1))
            percent = min(99, int(copied * 100 / iso_size)) if iso_size else 0
            self.progress_signal.emit(percent)
            if percent >= last_logged + 5:
                self.log_signal.emit(
                    f"   {size_gib(copied):.2f} GiB escritos ({percent}%)"
                )
                return percent
            return last_logged

        self.log_signal.emit(text)
        return last_logged
