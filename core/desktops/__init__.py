"""Motor Fedora Desktop independiente del motor Kiosco.

Este paquete describe entornos de escritorio convencionales y genera su
Kickstart sin reutilizar ``KioskISOBuilder``. La integración con la interfaz y
la ejecución de ``livecd-creator`` se realiza en una etapa posterior.
"""
from core.desktops.environments import (
    DESKTOP_ENVIRONMENTS,
    UnknownDesktopEnvironmentError,
    desktop_environment_keys,
    get_desktop_environment,
    list_desktop_environments,
    supported_display_servers,
)
from core.desktops.hardware import (
    HARDWARE_MODULES,
    UnknownHardwareModuleError,
    get_hardware_module,
    hardware_module_keys,
    list_hardware_modules,
    resolve_hardware_packages,
)
from core.desktops.packages import (
    DesktopPackageError,
    KIOSK_ONLY_ENTRIES,
    resolve_desktop_packages,
    validate_group_names,
    validate_package_names,
)
from core.desktops.kickstart import (
    DesktopKickstartError,
    DesktopKickstartGenerator,
)

__all__ = [
    "DESKTOP_ENVIRONMENTS",
    "DesktopKickstartError",
    "DesktopKickstartGenerator",
    "DesktopPackageError",
    "HARDWARE_MODULES",
    "KIOSK_ONLY_ENTRIES",
    "UnknownDesktopEnvironmentError",
    "UnknownHardwareModuleError",
    "desktop_environment_keys",
    "get_desktop_environment",
    "get_hardware_module",
    "hardware_module_keys",
    "list_desktop_environments",
    "list_hardware_modules",
    "resolve_desktop_packages",
    "resolve_hardware_packages",
    "validate_group_names",
    "validate_package_names",
]
