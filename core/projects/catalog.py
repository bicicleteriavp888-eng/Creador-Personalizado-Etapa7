"""Perfiles iniciales para el asistente de creación de distribuciones.

Los paquetes son sugerencias del perfil, no una promesa de disponibilidad:
la resolución final siempre corresponde a DNF en los repositorios elegidos.
"""
from __future__ import annotations

import re
from copy import deepcopy

_PACKAGE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")

PROJECT_TYPES = {
    "kiosk": {
        "name": "Kiosco / terminal",
        "tagline": "Un equipo dedicado a una aplicación o portal.",
        "description": "Arranque directo, interfaz controlada y pocas distracciones. Ideal para atención al público, cartelería y terminales.",
        "icon": "🖥️",
        "packages": ["chromium", "NetworkManager", "NetworkManager-wifi", "wpa_supplicant", "linux-firmware"],
        "groups": ["Aplicación principal", "Conectividad", "Acceso restringido"],
        "engine": "kiosk",
        "defaults": {
            "boot_mode": "dual", "app_mode": "chromium", "app_url": "http://localhost",
            "multi_app": False, "app2_mode": "firefox-es", "enable_firewall": True,
            "enable_ssh": False, "sudo_nopasswd": False, "block_vt": True,
            "enable_installer": True, "desktop_environment": "gnome",
        },
    },
    "office": {
        "name": "Oficina / productividad",
        "tagline": "Documentos, navegación, correo y videollamadas.",
        "description": "Base para un escritorio de trabajo con suite ofimática, navegador, PDF y utilidades cotidianas.",
        "icon": "📄",
        "packages": ["libreoffice-writer", "libreoffice-calc", "libreoffice-impress", "firefox", "evince", "NetworkManager-wifi", "linux-firmware"],
        "groups": ["Ofimática", "Internet", "Documentos"],
        "engine": "desktop",
        "defaults": {
            "boot_mode": "dual", "desktop_environment": "gnome", "desktop_user": "fedora",
            "enable_firewall": True, "enable_ssh": False, "sudo_nopasswd": False,
            "enable_installer": True, "multi_app": False,
        },
    },
    "web": {
        "name": "Web / servicios",
        "tagline": "Una base para desarrollo y despliegue web.",
        "description": "Herramientas para crear, probar y administrar aplicaciones web. Los servicios se mantienen desactivados hasta que el usuario los habilite.",
        "icon": "🌐",
        "packages": ["git", "python3", "python3-pip", "nodejs", "npm", "nginx", "sqlite", "curl", "firefox"],
        "groups": ["Desarrollo", "Servidor web opcional", "Pruebas"],
        "engine": "desktop",
        "defaults": {
            "boot_mode": "dual", "desktop_environment": "xfce", "desktop_user": "developer",
            "enable_firewall": True, "enable_ssh": False, "sudo_nopasswd": False,
            "enable_installer": True, "multi_app": False,
        },
    },
    "gaming": {
        "name": "Gaming / multimedia",
        "tagline": "Gráficos, audio, mandos y juegos disponibles en Fedora.",
        "description": "Base multimedia y herramientas de juegos de los repositorios configurados. Steam y otros catálogos externos requieren repositorios y licencias adicionales.",
        "icon": "🎮",
        "packages": ["mesa-dri-drivers", "mesa-vulkan-drivers", "vulkan-loader", "gamemode", "SDL2", "pipewire", "pavucontrol", "supertuxkart"],
        "groups": ["Gráficos y Vulkan", "Audio", "Juegos"],
        "engine": "desktop",
        "defaults": {
            "boot_mode": "dual", "desktop_environment": "kde", "desktop_user": "gamer",
            "enable_firewall": True, "enable_ssh": False, "sudo_nopasswd": False,
            "enable_installer": True, "multi_app": False,
        },
    },
    "security_lab": {
        "name": "Laboratorio de ciberseguridad",
        "tagline": "Auditoría defensiva, análisis y aprendizaje en entornos autorizados.",
        "description": "Herramientas de diagnóstico, captura y evaluación defensiva. No habilita servicios de red ni ejecuta pruebas automáticamente.",
        "icon": "🛡️",
        "packages": ["nmap", "wireshark", "tcpdump", "traceroute", "bind-utils", "openscap-scanner", "scap-security-guide", "lynis", "git", "python3"],
        "groups": ["Diagnóstico de red", "Análisis", "Auditoría defensiva"],
        "engine": "desktop",
        "defaults": {
            "boot_mode": "dual", "desktop_environment": "xfce", "desktop_user": "analyst",
            "enable_firewall": True, "enable_ssh": False, "sudo_nopasswd": False,
            "enable_installer": True, "multi_app": False,
        },
    },
    "custom": {
        "name": "Distribución personalizada",
        "tagline": "Empezar desde una selección vacía.",
        "description": "Elegí manualmente el software y los componentes que necesitás.",
        "icon": "🧩",
        "packages": [],
        "groups": ["Selección manual"],
        "engine": "desktop",
        "defaults": {
            "boot_mode": "dual", "desktop_environment": "gnome", "desktop_user": "fedora",
            "enable_firewall": True, "enable_ssh": False, "sudo_nopasswd": False,
            "enable_installer": True, "multi_app": False,
        },
    },
}


def list_project_types():
    return [(key, value["name"], value["tagline"]) for key, value in PROJECT_TYPES.items()]


def get_project_template(project_type: str) -> dict:
    """Devuelve una copia aislada del perfil o falla con un mensaje claro."""
    key = str(project_type or "").strip().lower()
    if key not in PROJECT_TYPES:
        raise ValueError(f"Tipo de proyecto desconocido: {key or '(vacío)'}")
    return deepcopy(PROJECT_TYPES[key])


def merge_packages(*groups) -> list[str]:
    """Normaliza, valida y deduplica paquetes preservando el orden."""
    result, seen = [], set()
    for group in groups:
        if isinstance(group, str):
            values = re.split(r"[\s,]+", group)
        else:
            values = group or []
        for value in values:
            package = str(value or "").strip()
            if not package:
                continue
            if not _PACKAGE_RE.fullmatch(package):
                raise ValueError(f"Nombre de paquete no válido: {package}")
            if package not in seen:
                seen.add(package)
                result.append(package)
    return result

# Perfiles nominales existentes del proyecto. Se leen desde profiles/*.json para
# mantener la configuración publicada en un único formato editable.
from pathlib import Path
import json
import sys

_NAMED_PROFILE_TYPES = {
    "estacion-trabajo": "web",
    "kiosco-multiventana": "kiosk",
    "kiosco-navegador": "kiosk",
    "oficina": "office",
    "terminal-atencion": "kiosk",
}


def list_named_profiles() -> list[dict]:
    """Lista los perfiles nominales versionados en profiles/*.json."""
    candidates = (
        Path(__file__).resolve().parents[2] / "profiles",
        Path(sys.prefix) / "share" / "creador-personalizado" / "profiles",
        Path.home() / ".local" / "share" / "creador-personalizado" / "profiles",
        Path("/usr/share/creador-personalizado/profiles"),
    )
    directory = next((item for item in candidates if item.is_dir()), candidates[0])
    profiles = []
    for path in sorted(directory.glob("*.json")):
        if path.name == "schema.json":
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            profile_id = path.stem
            if profile_id not in _NAMED_PROFILE_TYPES:
                continue
            profiles.append({
                "id": profile_id,
                "name": str(payload.get("profile_name") or profile_id),
                "description": str(payload.get("description") or ""),
                "project_type": _NAMED_PROFILE_TYPES[profile_id],
                "config": deepcopy(payload.get("config") or {}),
            })
        except (OSError, ValueError, TypeError):
            continue
    order = {"terminal-atencion": 0, "kiosco-navegador": 1, "kiosco-multiventana": 2, "oficina": 3, "estacion-trabajo": 4}
    return sorted(profiles, key=lambda item: order.get(item["id"], 99))


def get_named_profile_template(profile_id: str) -> dict:
    """Combina una plantilla funcional con los valores del perfil nominal."""
    key = str(profile_id or "").strip().lower()
    profile = next((item for item in list_named_profiles() if item["id"] == key), None)
    if profile is None:
        raise ValueError(f"Perfil nominal desconocido: {key or '(vacío)'}")
    template = get_project_template(profile["project_type"])
    template["profile_id"] = profile["id"]
    template["name"] = profile["name"]
    template["description"] = profile["description"]
    template["defaults"].update(profile["config"])
    return template
