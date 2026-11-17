"""Módulos de compatibilidad de hardware para el motor Fedora Desktop.

Los módulos representan capacidades que se agregan a la selección de paquetes
según el entorno de escritorio. Se aplican solamente con el motor Desktop: el
motor Kiosco no incorpora módulos de este catálogo porque define su propia
arquitectura de arranque restringida.

Cada módulo declara:

* ``packages``: paquetes RPM que aportan la capacidad;
* ``environments``: entornos del catálogo a los que aplica;
* ``enabled``: si el módulo forma parte de la base del entorno.

El asistente de conexión Wi-Fi en la sesión Live se modela con el módulo
``wifi_live_assistant``, que garantiza los paquetes de red inalambrica y el
gestor de conexiones disponibles en la ISO.
"""
from __future__ import annotations

from copy import deepcopy

from core.desktops.environments import get_desktop_environment
from core.desktops.packages import (
    KIOSK_ONLY_ENTRIES,
    DesktopPackageError,
)
from core.software.policy import (
    validate_package_names,
)

HARDWARE_MODULE_ORDER = (
    "graphics",
    "wifi",
    "touchpad",
    "wifi_live_assistant",
)

HARDWARE_MODULES = {
    "graphics": {
        "name": "Gráficos",
        "description": (
            "Controladores DRI/EGL y OpenGL para la GPU del equipo de destino."
        ),
        "environments": ("gnome", "kde", "xfce"),
        "packages": [
            "mesa-dri-drivers",
            "mesa-libEGL",
            "libglvnd-egl",
        ],
        "enabled": True,
    },
    "wifi": {
        "name": "Red Wi-Fi",
        "description": (
            "Red inalambrica con NetworkManager, WPA supplicant, iw y linux-firmware."
        ),
        "environments": ("gnome", "kde", "xfce"),
        "packages": [
            "NetworkManager",
            "NetworkManager-wifi",
            "wpa_supplicant",
            "iw",
            "linux-firmware",
        ],
        "enabled": True,
    },
    "touchpad": {
        "name": "Touchpad",
        "description": "Backend libinput para touchpad y perifericos táctiles.",
        "environments": ("gnome", "kde", "xfce"),
        "packages": ["libinput"],
        "enabled": True,
    },
    "wifi_live_assistant": {
        "name": "Asistente de conexión Wi-Fi en Live",
        "description": (
            "Gestor de conexiones inalámbricas disponible en la sesión Live."
        ),
        "environments": ("gnome", "kde", "xfce"),
        "packages": [
            "NetworkManager",
            "NetworkManager-wifi",
            "wpa_supplicant",
            "iw",
            "linux-firmware",
        ],
        "enabled": True,
    },
}


class UnknownHardwareModuleError(ValueError):
    """El módulo de hardware solicitado no existe en el catálogo."""


def hardware_module_keys():
    """Devuelve las claves válidas de módulos de hardware en orden."""
    return tuple(HARDWARE_MODULES)


def list_hardware_modules():
    """Lista ``(clave, nombre, descripcion)`` para la interfaz."""
    return [
        (
            key,
            value["name"],
            value["description"],
        )
        for key, value in HARDWARE_MODULES.items()
    ]


def get_hardware_module(module_key):
    """Devuelve una copia aislada del módulo o falla con mensaje claro."""
    key = str(module_key or "").strip().lower()
    if key not in HARDWARE_MODULES:
        valid = ", ".join(HARDWARE_MODULES)
        raise UnknownHardwareModuleError(
            f"Módulo de hardware desconocido: {key or '(vacío)'}. "
            f"Módulos disponibles: {valid}."
        )
    return deepcopy(HARDWARE_MODULES[key])


def resolve_hardware_packages(
    environment_key,
    modules=None,
    wifi_live_assistant=False,
):
    """Resuelve los paquetes de hardware del entorno.

    Devuelve una lista plana de nombres de paquete validados, sin duplicados y
    sin componentes exclusivos del motor Kiosco. ``modules`` selecciona los
    módulos por clave; ``wifi_live_assistant`` habilita el asistente de Wi-Fi en
    la sesión Live sin necesidad de nombrar el módulo explícitamente.
    """
    environment = get_desktop_environment(environment_key)

    selected = []
    if wifi_live_assistant:
        selected.append("wifi_live_assistant")
    for module_key in modules or ():
        module_key = str(module_key or "").strip().lower()
        if module_key and module_key not in selected:
            selected.append(module_key)
    for module_key in selected:
        if module_key not in HARDWARE_MODULES:
            raise UnknownHardwareModuleError(
                f"Módulo de hardware desconocido: {module_key}."
            )

    entries = []
    for module_key in HARDWARE_MODULE_ORDER:
        if module_key not in selected:
            continue
        module = HARDWARE_MODULES[module_key]
        if str(environment_key) not in module["environments"]:
            continue
        entries.extend(module["packages"])

    result = validate_package_names(entries)
    problems = []
    if result["invalid"]:
        problems.append(
            "nombres inválidos: " + ", ".join(f"'{value}'" for value in result["invalid"])
        )
    if result["blocked"]:
        problems.append(
            "bloqueados por política de seguridad: " + ", ".join(result["blocked"])
        )
    if problems:
        raise DesktopPackageError(
            "Selección de hardware rechazada: " + "; ".join(problems)
        )

    allowed = result["allowed"]
    seen, unique = set(), []
    for entry in allowed:
        if entry not in seen:
            seen.add(entry)
            unique.append(entry)
    kiosk_entries = sorted(set(unique) & set(KIOSK_ONLY_ENTRIES))
    if kiosk_entries:
        raise DesktopPackageError(
            "El motor Desktop no puede incluir componentes exclusivos de "
            "Kiosco: " + ", ".join(kiosk_entries)
        )
    return unique
