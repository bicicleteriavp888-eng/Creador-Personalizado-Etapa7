"""Escáner no invasivo de hardware PCI/USB y perfiles reutilizables.

El escáner no instala controladores ni habilita repositorios. Sugiere paquetes
base de Fedora y marca los controladores de terceros como acciones manuales.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timezone

PROFILE_VERSION = 1


def _run(command: list[str]) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=15,
            stdin=subprocess.DEVNULL, check=False,
        )
        return result.returncode, result.stdout or "", result.stderr or ""
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, "", str(exc)


def _pci_devices(text: str) -> list[dict]:
    devices, current = [], None
    for line in (text or "").splitlines():
        if line and not line[0].isspace() and re.match(r"^[0-9a-fA-F:.]+\s", line):
            if current:
                devices.append(current)
            current = {"address": line.split()[0], "description": line.strip(),
                       "vendor_device": ""}
            match = re.search(r"\[([0-9a-fA-F]{4}):([0-9a-fA-F]{4})\]", line)
            if match:
                current["vendor_device"] = f"{match.group(1).lower()}:{match.group(2).lower()}"
        elif current and "Kernel driver in use:" in line:
            current["driver"] = line.split(":", 1)[1].strip()
        elif current and "Kernel modules:" in line:
            current["kernel_modules"] = line.split(":", 1)[1].strip()
    if current:
        devices.append(current)
    return devices


def _usb_devices(text: str) -> list[dict]:
    result = []
    for line in (text or "").splitlines():
        match = re.search(r"ID ([0-9a-fA-F]{4}):([0-9a-fA-F]{4})\s+(.*)", line)
        if match:
            result.append({
                "vendor_device": f"{match.group(1).lower()}:{match.group(2).lower()}",
                "description": match.group(3).strip(),
            })
    return result


def _recommend(devices: list[dict]) -> list[dict]:
    recommendations = {}
    for device in devices:
        desc = device.get("description", "").lower()
        vid = device.get("vendor_device", "").split(":")[0]
        if any(token in desc for token in ("network", "wireless", "wi-fi", "ethernet")):
            for package in ("NetworkManager-wifi", "wpa_supplicant", "iw", "linux-firmware"):
                recommendations[package] = {
                    "package": package, "reason": "Conectividad de red detectada",
                    "confidence": "base Fedora", "requires_external_repo": False,
                }
            if vid == "14e4":
                recommendations["akmod-wl"] = {
                    "package": "akmod-wl",
                    "reason": "Adaptador Broadcom detectado; controlador propietario posible",
                    "confidence": "manual", "requires_external_repo": True,
                    "note": "Requiere RPM Fusion y confirmar el identificador exacto del chipset.",
                }
        if any(token in desc for token in ("vga", "3d controller", "display controller")):
            for package in ("mesa-dri-drivers", "mesa-libEGL", "linux-firmware"):
                recommendations[package] = {
                    "package": package, "reason": "Pila gráfica libre y firmware",
                    "confidence": "base Fedora", "requires_external_repo": False,
                }
            if vid == "10de":
                recommendations["akmod-nvidia"] = {
                    "package": "akmod-nvidia",
                    "reason": "GPU NVIDIA detectada; controlador propietario opcional",
                    "confidence": "manual",
                    "requires_external_repo": True,
                    "note": "Requiere RPM Fusion y debe verificarse para la versión/kernel destino.",
                }
            elif vid == "14e4":
                recommendations["broadcom-wl"] = {
                    "package": "akmod-wl",
                    "reason": "Hardware Broadcom; controlador propietario posible",
                    "confidence": "manual",
                    "requires_external_repo": True,
                    "note": "No se agrega automáticamente: requiere RPM Fusion y validación del chipset.",
                }
    return list(recommendations.values())


def scan_hardware() -> dict:
    """Inspecciona lspci -nnk y lsusb sin realizar cambios en el host."""
    commands = {}
    pci_text = ""
    usb_text = ""
    for name, args in (
        ("lspci", ["lspci", "-nnk"]),
        ("lsusb", ["lsusb"]),
    ):
        if not shutil.which(args[0]):
            commands[name] = {"available": False, "returncode": 127, "error": f"{args[0]} no está instalado."}
            continue
        rc, out, err = _run(args)
        commands[name] = {"available": True, "returncode": rc, "error": err.strip()}
        if name == "lspci":
            pci_text = out
        else:
            usb_text = out
    pci = _pci_devices(pci_text)
    usb = _usb_devices(usb_text)
    devices = pci + usb
    return {
        "schema_version": PROFILE_VERSION,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "host": {"kernel": _run(["uname", "-r"])[1].strip() if shutil.which("uname") else ""},
        "commands": commands,
        "pci_devices": pci,
        "usb_devices": usb,
        "recommendations": _recommend(devices),
        "notice": "Las recomendaciones son orientativas. No se instalaron paquetes ni se habilitaron repositorios.",
    }


def export_hardware_profile(path: str | Path, scan: dict, name: str,
                            resolution: str = "auto", selected_packages: list[str] | None = None) -> Path:
    if not str(name or "").strip():
        raise ValueError("El perfil necesita un nombre.")
    payload = {
        "schema_version": PROFILE_VERSION,
        "name": str(name).strip()[:100],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "resolution": str(resolution or "auto"),
        "selected_packages": list(dict.fromkeys(selected_packages or [])),
        "hardware": scan,
    }
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def load_hardware_profile(path: str | Path) -> dict:
    payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != PROFILE_VERSION:
        raise ValueError("Formato o versión de perfil de hardware no compatible.")
    packages = payload.get("selected_packages", [])
    if not isinstance(packages, list) or not all(
        isinstance(item, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", item)
        for item in packages
    ):
        raise ValueError("El perfil contiene nombres de paquetes inválidos.")
    return payload
