"""Catálogo de entornos de escritorio Fedora para el motor Desktop.

Este módulo es independiente del motor Kiosco: no importa Qt, no genera
imágenes y no conoce ``cage``, ``sway``, ``seatd`` ni ``kioskuser``. Solo
describe qué paquetes, grupo de paquetes y gestor de sesión corresponden a
cada entorno.

Los nombres son selecciones iniciales. La disponibilidad real y la resolución
de dependencias siguen siendo responsabilidad de DNF en los repositorios
configurados al compilar.
"""
from __future__ import annotations

from copy import deepcopy

DESKTOP_ENVIRONMENTS = {
    "gnome": {
        "name": "GNOME",
        "tagline": "Escritorio GNOME con sesión Wayland.",
        "description": (
            "Entorno GNOME completo con GDM, ajustes del sistema, archivos, "
            "terminal y navegador. Es la experiencia predeterminada de Fedora "
            "Workstation."
        ),
        "session_manager": "GDM",
        "display_manager": "gdm",
        "display_manager_unit": "gdm",
        "display_manager_service": "gdm.service",
        "session_type": "wayland",
        "supported_display_servers": ["wayland"],
        "groups": ["@gnome-desktop"],
        "packages": [
            "gdm",
            "gnome-shell",
            "gnome-session",
            "gnome-control-center",
            "gnome-terminal",
            "nautilus",
            "gnome-disk-utility",
            "gnome-system-monitor",
            "file-roller",
            "evince",
            "gnome-text-editor",
            "firefox",
        ],
    },
    "kde": {
        "name": "KDE Plasma",
        "tagline": "Escritorio Plasma con sesión Wayland.",
        "description": (
            "Entorno KDE Plasma con SDDM, aplicaciones Plasma, terminal, "
            "gestor de archivos y navegador. Adecuado para equipos con "
            "preferencias de personalización intensiva."
        ),
        "session_manager": "SDDM",
        "display_manager": "sddm",
        "display_manager_unit": "sddm",
        "display_manager_service": "sddm.service",
        "session_type": "wayland",
        # Fedora 44 actualiza Plasma a Wayland-only en las versiones actuales.
        "supported_display_servers": ["wayland"],
        "groups": ["@kde-desktop"],
        "packages": [
            "sddm",
            "plasma-workspace",
            "plasma-desktop",
            "plasma-nm",
            "kf6-kwallet",
            "konsole",
            "dolphin",
            "kate",
            "ark",
            "firefox",
        ],
    },
    "xfce": {
        "name": "Xfce",
        "tagline": "Escritorio liviano con LightDM.",
        "description": (
            "Entorno Xfce con LightDM, panel, terminal y gestor de archivos. "
            "Pensado para equipos con recursos limitados o hardware heredado "
            "que necesita un escritorio tradicional sobre X11."
        ),
        "session_manager": "LightDM",
        "display_manager": "lightdm",
        "display_manager_unit": "lightdm",
        "display_manager_service": "lightdm.service",
        "session_type": "x11",
        "supported_display_servers": ["x11"],
        "groups": ["@xfce-desktop"],
        "packages": [
            "lightdm",
            "lightdm-gtk",
            "xfce4-session",
            "xfwm4",
            "xfce4-panel",
            "xfce4-settings",
            "xfce4-terminal",
            "xfce4-power-manager",
            "xfce4-notifyd",
            "thunar",
            "xorg-x11-server-Xorg",
            "xorg-x11-drv-libinput",
            "xorg-x11-xinit",
            "firefox",
        ],
    },
}


class UnknownDesktopEnvironmentError(ValueError):
    """El entorno solicitado no existe en el catálogo del motor Desktop."""


def desktop_environment_keys():
    """Devuelve las claves válidas en el orden del catálogo."""
    return tuple(DESKTOP_ENVIRONMENTS)


def list_desktop_environments():
    """Lista ``(clave, nombre, gestor de sesión)`` para la interfaz."""
    return [
        (key, value["name"], value["session_manager"])
        for key, value in DESKTOP_ENVIRONMENTS.items()
    ]


def supported_display_servers(environment_key):
    """Devuelve los servidores gráficos realmente disponibles en Fedora 44."""
    return tuple(get_desktop_environment(environment_key)["supported_display_servers"])


def get_desktop_environment(environment_key):
    """Devuelve una copia aislada del entorno o falla con un mensaje claro."""
    key = str(environment_key or "").strip().lower()
    if key not in DESKTOP_ENVIRONMENTS:
        valid = ", ".join(DESKTOP_ENVIRONMENTS)
        raise UnknownDesktopEnvironmentError(
            f"Entorno de escritorio desconocido: {key or '(vacío)'}. "
            f"Entornos disponibles: {valid}."
        )
    return deepcopy(DESKTOP_ENVIRONMENTS[key])
