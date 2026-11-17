"""Políticas compartidas de validación para selección de software.

Las reglas son deliberadamente estrictas y separadas por tipo de entrada:

* **paquetes**: nombres RPM ordinarios, sin ``@``.
* **grupos**: entradas comps como ``@office`` o
  ``@^workstation-product-environment``.
* **búsqueda**: texto libre acotado que nunca se interpreta como opción de
  DNF y que jamás se pasa a una shell.

El objetivo es que la interfaz, el motor Desktop y los adaptadores DNF
rechacen las mismas entradas antes de ejecutar cualquier comando.
"""
from __future__ import annotations

import re

from core.security.allowlist import BLOCKED_PACKAGES, RPM_NAME_PATTERN

PACKAGE_NAME_MAX = 128
GROUP_NAME_MAX = 64
SEARCH_QUERY_MAX = 120

GROUP_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")
GROUP_NAME_PATTERN = re.compile(r"^@\^?[A-Za-z0-9][A-Za-z0-9._+-]*$")


class SoftwareSelectionError(ValueError):
    """Entrada de software inválida o bloqueada por política."""


def split_entries(raw):
    """Normaliza una cadena o colección separada por espacios o comas."""
    if raw is None:
        return []
    if isinstance(raw, str):
        return [entry for entry in re.split(r"[\s,]+", raw) if entry]
    entries = []
    for value in raw:
        entry = str(value or "").strip()
        if entry:
            entries.append(entry)
    return entries


def _package_name_is_valid(entry):
    return len(entry) <= PACKAGE_NAME_MAX and bool(
        RPM_NAME_PATTERN.fullmatch(entry)
    )


def _group_name_is_valid(entry):
    return len(entry) <= GROUP_NAME_MAX and bool(
        GROUP_NAME_PATTERN.fullmatch(entry)
    )


def validate_package_names(raw):
    """Valida una selección como nombres de paquete (sin ``@``).

    Devuelve ``{"allowed", "blocked", "invalid"}`` conservando el orden. Un
    nombre de grupo como ``@gnome-desktop`` cae en ``invalid`` a propósito:
    para grupos existe :func:`validate_group_names`.
    """
    allowed, blocked, invalid = [], [], []
    for entry in split_entries(raw):
        if entry in BLOCKED_PACKAGES:
            blocked.append(entry)
        elif _package_name_is_valid(entry):
            allowed.append(entry)
        else:
            invalid.append(entry)
    return {"allowed": allowed, "blocked": blocked, "invalid": invalid}


def validate_group_names(raw):
    """Valida una selección como grupos comps (deben empezar con ``@``)."""
    allowed, invalid = [], []
    for entry in split_entries(raw):
        if _group_name_is_valid(entry):
            allowed.append(entry)
        else:
            invalid.append(entry)
    return {"allowed": allowed, "invalid": invalid}


def normalize_package_entry(value):
    """Valida y devuelve un único nombre de paquete."""
    entry = str(value or "").strip()
    if not entry:
        raise SoftwareSelectionError("El nombre del paquete no puede estar vacío.")
    if len(entry) > PACKAGE_NAME_MAX:
        raise SoftwareSelectionError(
            f"El nombre del paquete supera {PACKAGE_NAME_MAX} caracteres."
        )
    if entry in BLOCKED_PACKAGES:
        raise SoftwareSelectionError(
            f"El paquete '{entry}' está bloqueado por política de seguridad."
        )
    if not RPM_NAME_PATTERN.fullmatch(entry):
        raise SoftwareSelectionError(
            f"Nombre de paquete inválido: '{entry}'. Usa solo letras, números, "
            "punto, guion, guion bajo o +, empezando por letra o número."
        )
    return entry


def normalize_packages(raw, label="paquetes"):
    """Valida, normaliza y deduplica una selección de paquetes.

    Lanza :class:`SoftwareSelectionError` con un resumen de todos los nombres
    inválidos o bloqueados; no descarta entradas en silencio.
    """
    result = validate_package_names(raw)
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
        raise SoftwareSelectionError(
            f"Selección de {label} rechazada: " + "; ".join(problems)
        )
    return _unique(result["allowed"])


def normalize_group_id(value):
    """Valida un identificador de grupo comps sin el prefijo ``@``."""
    entry = str(value or "").strip()
    if not entry:
        raise SoftwareSelectionError("El identificador del grupo no puede estar vacío.")
    if len(entry) > GROUP_NAME_MAX:
        raise SoftwareSelectionError(
            f"El identificador del grupo supera {GROUP_NAME_MAX} caracteres."
        )
    if not GROUP_ID_PATTERN.fullmatch(entry):
        raise SoftwareSelectionError(
            f"Identificador de grupo inválido: '{entry}'. Usa solo letras, "
            "números, punto, guion, guion bajo o +."
        )
    return entry


def normalize_group_entry(value):
    """Normaliza ``office``, ``@office`` o ``@^office`` a una entrada comps."""
    entry = str(value or "").strip()
    if entry.startswith("@^"):
        prefix, identifier = "@^", entry[2:]
    elif entry.startswith("@"):
        prefix, identifier = "@", entry[1:]
    else:
        prefix, identifier = "@", entry
    return prefix + normalize_group_id(identifier)


def normalize_groups(raw, label="grupos"):
    """Normaliza, valida y deduplica una selección de grupos comps."""
    normalized, problems = [], []
    for entry in split_entries(raw):
        try:
            normalized.append(normalize_group_entry(entry))
        except SoftwareSelectionError as exc:
            problems.append(str(exc))
    if problems:
        raise SoftwareSelectionError(
            f"Selección de {label} rechazada: " + " ".join(problems)
        )
    return _unique(normalized)


def normalize_search_query(query):
    """Valida el texto de búsqueda de DNF.

    Devuelve la cadena sin espacios extremos. La cadena vacía es válida y
    significa ``catálogo completo``. Se rechazan controles, saltos de línea y
    textos que empiecen con ``-`` para que nunca puedan confundirse con una
    opción de DNF.
    """
    text = str(query or "").strip()
    if len(text) > SEARCH_QUERY_MAX:
        raise SoftwareSelectionError(
            f"La búsqueda admite hasta {SEARCH_QUERY_MAX} caracteres."
        )
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in text):
        raise SoftwareSelectionError(
            "La búsqueda no puede contener caracteres de control ni saltos de línea."
        )
    if text.startswith("-") or any(term.startswith("-") for term in text.split()):
        raise SoftwareSelectionError(
            "La búsqueda no puede contener términos que empiecen con guion."
        )
    return text


def _unique(values):
    seen, result = set(), []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
