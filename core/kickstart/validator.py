"""Validador de sintaxis y directivas Kickstart para Creador-kiosk 2.0."""

import re


def validate_kickstart_content(ks_text):
    """Valida la sintaxis básica y directivas obligatorias de un archivo Kickstart.

    Devuelve una lista de tuplas (tipo, mensaje) donde tipo es 'error' o 'warning'.
    """
    issues = []
    if not ks_text or not ks_text.strip():
        issues.append(("error", "El contenido Kickstart está vacío."))
        return issues

    # Comprobar directivas esenciales
    if "text" not in ks_text:
        issues.append(("warning", "No se encontró la directiva 'text' (modo texto)."))
    if "bootloader" not in ks_text:
        issues.append(("error", "Falta la directiva 'bootloader'."))
    if "clearpart" not in ks_text:
        issues.append(("warning", "No se encontró 'clearpart'."))
    if "%packages" not in ks_text:
        issues.append(("error", "Falta la sección '%packages'."))
    if "%post" not in ks_text:
        issues.append(("error", "Falta la sección '%post'."))
    elif "--erroronfail" not in ks_text:
        issues.append(("warning", "La sección '%post' no incluye '--erroronfail'."))

    # Comprobar particionamiento root
    if not re.search(r"part\s+/\s+", ks_text):
        issues.append(("error", "No se encontró partición para la raíz '/'."))

    return issues
