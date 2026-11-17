"""Constantes y utilidades compartidas de Creador Personalizado.

Las rutas históricas creador-kiosk se conservan temporalmente para no romper
proyectos, cachés y compilaciones existentes durante la migración 3.0.
"""

import re

FEDORA_RELEASE = "44"
FEDORA_ARCH = "x86_64"

# Por defecto se usa el mirrorlist oficial: dnf elige mirrors cercanos y hace
# failover automatico si uno falla. KIOSK_MIRROR fuerza un mirror fijo con
# layout Fedora (releases/ + updates/), por ejemplo para un mirror local.
DEFAULT_MIRRORLIST = "https://mirrors.fedoraproject.org/mirrorlist"

# livecd-creator necesita varios GiB para el arbol de instalacion y la ISO.
# /var/tmp esta respaldado por disco (a diferencia de /tmp, que en Fedora es
# tmpfs y consume RAM).
BUILD_ROOT = "/var/tmp/creador-kiosk"
CACHE_ROOT = "/var/cache/creador-kiosk"
DEFAULT_OUTPUT_DIR = "~/ISOs"

MIN_FREE_BYTES = 12 * 1024 ** 3
MAX_PLYMOUTH_BYTES = 4 * 1024 * 1024

def sanitize(text, maxlen, fallback):
    """Deja solo caracteres seguros para labels/nombres de archivo."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", (text or "").strip())
    cleaned = cleaned.strip("-._")
    return cleaned[:maxlen] or fallback


def dedupe(items):
    """Devuelve los elementos sin repetir, conservando el orden."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
