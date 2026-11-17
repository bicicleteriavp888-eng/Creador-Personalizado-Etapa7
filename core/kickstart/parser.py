"""Analizador de archivos Kickstart para Creador-kiosk 2.0."""

import re


def parse_packages_from_kickstart(ks_text):
    """Extrae la lista de paquetes declarados en la sección %packages."""
    packages = []
    in_packages = False
    for line in ks_text.splitlines():
        line = line.strip()
        if line == "%packages":
            in_packages = True
            continue
        elif line == "%end" and in_packages:
            in_packages = False
            continue
        if in_packages and line and not line.startswith("#"):
            packages.append(line)
    return packages
