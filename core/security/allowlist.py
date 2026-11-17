"""Listas de paquetes permitidos y bloqueados para Creador-kiosk 2.0."""

import re

# Paquetes prohibidos por seguridad o inestabilidad en kioscos
BLOCKED_PACKAGES = {
    "telnet",
    "rsh",
    "rsh-server",
    "nis",
    "ypbind",
    "tftp",
    "tftp-server",
}

# Patrón estricto para nombres de paquetes RPM válidos
RPM_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")


def is_package_allowed(pkg_name):
    """Verifica si un paquete está permitido y no figura en la lista negra."""
    pkg_name = (pkg_name or "").strip()
    if not pkg_name:
        return False
    if pkg_name in BLOCKED_PACKAGES:
        return False
    return bool(RPM_NAME_PATTERN.fullmatch(pkg_name))


def validate_packages_list(packages_str):
    """Valida una cadena separada por espacios/comas de paquetes."""
    allowed = []
    blocked = []
    invalid = []
    for raw in re.split(r"[\s,]+", packages_str or ""):
        if not raw:
            continue
        if raw in BLOCKED_PACKAGES:
            blocked.append(raw)
        elif RPM_NAME_PATTERN.fullmatch(raw):
            allowed.append(raw)
        else:
            invalid.append(raw)
    return {"allowed": allowed, "blocked": blocked, "invalid": invalid}
