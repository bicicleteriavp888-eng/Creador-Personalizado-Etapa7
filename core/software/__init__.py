"""Selección de software compartida por los motores Kiosco y Desktop.

La validación vive en :mod:`core.software.policy` para que la interfaz, el
motor Desktop y los futuros adaptadores DNF apliquen exactamente las mismas
reglas. El catálogo de aplicaciones y los perfiles de proyecto siguen en
:mod:`core.projects`.
"""
from core.software.policy import (
    GROUP_ID_PATTERN,
    GROUP_NAME_PATTERN,
    GROUP_NAME_MAX,
    PACKAGE_NAME_MAX,
    SEARCH_QUERY_MAX,
    SoftwareSelectionError,
    normalize_group_entry,
    normalize_group_id,
    normalize_groups,
    normalize_package_entry,
    normalize_packages,
    normalize_search_query,
    split_entries,
    validate_group_names,
    validate_package_names,
)

__all__ = [
    "GROUP_ID_PATTERN",
    "GROUP_NAME_PATTERN",
    "GROUP_NAME_MAX",
    "PACKAGE_NAME_MAX",
    "SEARCH_QUERY_MAX",
    "SoftwareSelectionError",
    "normalize_group_entry",
    "normalize_group_id",
    "normalize_groups",
    "normalize_package_entry",
    "normalize_packages",
    "normalize_search_query",
    "split_entries",
    "validate_group_names",
    "validate_package_names",
]
