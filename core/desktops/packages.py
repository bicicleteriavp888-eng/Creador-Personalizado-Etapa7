"""Políticas de paquetes y grupos para el motor Fedora Desktop.

Se mantienen dos políticas separadas:

* **paquetes**: nombres RPM ordinarios. Nunca aceptan el prefijo ``@``.
* **grupos**: entradas de comps como ``@gnome-desktop`` o
  ``@^workstation-product-environment``.

La separación evita que una entrada de grupo se cuele como paquete, o que un
nombre de paquete se interprete como grupo por accidente. Los paquetes
bloqueados por seguridad y los nombres inválidos se rechazan con un error
explícito; no se descartan en silencio.

Los módulos de compatibilidad de hardware (gráficos, Wi-Fi, touchpad y asistente
Live) se resuelven con :mod:`core.desktops.hardware` y solo se incorporan cuando
el constructor los solicita.
"""
from __future__ import annotations

import re

from core.desktops.environments import get_desktop_environment
from core.software.policy import (
    GROUP_NAME_PATTERN,
    split_entries,
    validate_group_names,
    validate_package_names,
)

# Entradas que pertenecen al motor Kiosco y no deben aparecer en una imagen de
# escritorio convencional. La lista se comprueba también sobre los paquetes
# base para detectar regresiones futuras.
KIOSK_ONLY_ENTRIES = frozenset(
    {
        "cage",
        "sway",
        "seatd",
        "kioskuser",
        "kiosk.service",
        "kiosk-app",
        "lightdm-elephant-greeter",
    }
)

SUPPORTED_BOOT_MODES = ("dual", "uefi", "bios")

BASE_GROUPS = ["@core"]

# Paquetes comunes a cualquier escritorio. No incluyen compositor Wayland de
# kiosco, seatd, kioskuser ni servicios de sesión restringida.
BASE_PACKAGES = [
    "kernel",
    "dracut",
    "dracut-live",
    "dracut-config-generic",
    "plymouth",
    "plymouth-system-theme",
    "kbd",
    "glibc-langpack-es",
    "authselect",
    "xorg-x11-server-Xwayland",
    "mesa-dri-drivers",
    "mesa-libEGL",
    "libglvnd-egl",
    "fontconfig",
    "dejavu-sans-fonts",
    "google-noto-sans-fonts",
    "pipewire",
    "pipewire-pulseaudio",
    "wireplumber",
    "alsa-utils",
]

NETWORK_PACKAGES = [
    "NetworkManager",
    "NetworkManager-wifi",
    "wpa_supplicant",
    "iw",
    "iproute",
    "linux-firmware",
]

ADMIN_PACKAGES = [
    "sudo",
    "shadow-utils",
]

INSTALLER_PACKAGES = [
    "anaconda",
    "anaconda-live",
    "anaconda-install-env-deps",
    "anaconda-widgets",
    "anaconda-webui",
    "firefox",
    "polkit",
    "gsettings-desktop-schemas",
]

UEFI_PACKAGES = [
    "shim-x64",
    "grub2-efi-x64",
    "grub2-efi-x64-cdboot",
    "grub2-tools",
]


class DesktopPackageError(ValueError):
    """Selección de paquetes o grupos inválida para el motor Desktop."""


def _unique(values):
    seen, result = set(), []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _reject_invalid(entries, label):
    result = validate_package_names(entries)
    problems = []
    if result["invalid"]:
        problems.append(
            "nombres inválidos: "
            + ", ".join(f"'{value}'" for value in result["invalid"])
        )
    if result["blocked"]:
        problems.append(
            "bloqueados por política de seguridad: "
            + ", ".join(result["blocked"])
        )
    if problems:
        raise DesktopPackageError(
            f"Selección de {label} rechazada: " + "; ".join(problems)
        )
    return result["allowed"]


def _reject_invalid_groups(entries, label):
    result = validate_group_names(entries)
    if result["invalid"]:
        raise DesktopPackageError(
            f"Grupo de paquetes inválido en {label}: "
            + ", ".join(f"'{value}'" for value in result["invalid"])
            + ". Los grupos deben empezar con @ y usar solo letras, "
            "números y . _ + -."
        )
    return result["allowed"]


def _assert_no_kiosk_entries(entries):
    found = sorted(set(entries) & KIOSK_ONLY_ENTRIES)
    if found:
        raise DesktopPackageError(
            "El motor Desktop no puede incluir componentes exclusivos de "
            "Kiosco: " + ", ".join(found)
        )


def resolve_desktop_packages(
    environment_key,
    extra_packages="",
    extra_groups=(),
    enable_firewall=True,
    enable_ssh=False,
    enable_installer=True,
    boot_mode="dual",
    hardware_modules=None,
    wifi_live_assistant=False,
    display_server=None,
):
    """Resuelve la selección de un entorno de escritorio.

    Devuelve una lista de ``(título, entradas)`` con grupos y paquetes ya
    validados y deduplicados. Lanza :class:`DesktopPackageError` ante una
    entrada inválida, bloqueada o perteneciente al motor Kiosco.

    ``hardware_modules`` y ``wifi_live_assistant`` habilitan módulos de
    compatibilidad de hardware (gráficos, Wi-Fi, touchpad y asistente Live);
    solo se aplican cuando se solicitan explícitamente.
    """
    environment = get_desktop_environment(environment_key)
    selected_display_server = str(
        display_server or environment["session_type"]
    ).strip().lower()
    supported_servers = tuple(environment["supported_display_servers"])
    if selected_display_server not in supported_servers:
        raise DesktopPackageError(
            f"El escritorio {environment['name']} no ofrece sesión "
            f"{selected_display_server or '(vacía)'} en Fedora 44. "
            f"Opciones disponibles: {', '.join(supported_servers)}."
        )

    mode = str(boot_mode or "dual").strip().lower()
    if mode not in SUPPORTED_BOOT_MODES:
        raise DesktopPackageError(
            f"Modo de arranque desconocido: {mode or '(vacío)'}. "
            f"Valores admitidos: {', '.join(SUPPORTED_BOOT_MODES)}."
        )

    selected_hardware = hardware_modules
    if isinstance(selected_hardware, str):
        selected_hardware = [
            entry for entry in re.split(r"[\s,]+", selected_hardware) if entry
        ]

    base_groups = _reject_invalid_groups(BASE_GROUPS, "base del sistema")
    environment_groups = _reject_invalid_groups(
        environment["groups"], f"escritorio {environment['name']}"
    )
    requested_groups = _reject_invalid_groups(extra_groups, "grupos adicionales")

    base_packages = _reject_invalid(BASE_PACKAGES, "paquetes base")
    network_packages = _reject_invalid(NETWORK_PACKAGES, "conectividad")
    admin_packages = _reject_invalid(ADMIN_PACKAGES, "administración")
    environment_package_names = list(environment["packages"])
    if environment_key == "kde" and selected_display_server == "wayland":
        environment_package_names.append("plasma-workspace-wayland")
    environment_packages = _reject_invalid(
        environment_package_names, f"escritorio {environment['name']}"
    )
    extra = _reject_invalid(extra_packages, "paquetes adicionales")

    if enable_firewall:
        admin_packages.append("firewalld")
    if enable_ssh:
        admin_packages.extend(["openssh-server", "openssh-clients"])

    installer = (
        _reject_invalid(INSTALLER_PACKAGES, "instalador") if enable_installer else []
    )
    uefi = _reject_invalid(UEFI_PACKAGES, "arranque UEFI") if mode in ("dual", "uefi") else []

    sections = [
        ("Base del sistema", base_groups + base_packages),
        (
            f"Escritorio {environment['name']} · {environment['session_manager']} · {selected_display_server.upper()}",
            environment_groups + environment_packages,
        ),
        ("Red y conectividad", network_packages),
        ("Administración y servicios", admin_packages),
        ("Instalador en disco", installer),
        ("Arranque UEFI", uefi),
    ]

    hardware_entries = []
    if hardware_modules or wifi_live_assistant:
        from core.desktops import hardware as desktop_hardware

        hardware_entries = desktop_hardware.resolve_hardware_packages(
            environment_key,
            modules=hardware_modules,
            wifi_live_assistant=wifi_live_assistant,
        )
    if hardware_entries:
        sections.append(("Hardware y compatibilidad", hardware_entries))

    sections.append(("Paquetes adicionales", extra))
    sections.append(("Grupos adicionales", requested_groups))

    seen, resolved = set(), []
    for title, entries in sections:
        unique = []
        for entry in entries:
            if entry not in seen:
                seen.add(entry)
                unique.append(entry)
        if unique:
            resolved.append((title, unique))

    _assert_no_kiosk_entries(seen)
    return resolved
