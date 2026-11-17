"""Validaciones y diagnostico independientes de la interfaz."""

from core.validation.diagnostics import (
    REQUIRED_BINARIES,
    REQUIRED_SYSlinux,
    check_dependencies,
    check_disk,
    disk_info,
    preflight,
    service_states,
)

__all__ = [
    "REQUIRED_BINARIES",
    "REQUIRED_SYSlinux",
    "check_dependencies",
    "check_disk",
    "disk_info",
    "preflight",
    "service_states",
]
