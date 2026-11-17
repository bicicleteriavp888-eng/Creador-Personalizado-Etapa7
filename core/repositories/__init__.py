"""Módulo de repositorios: mirror Fedora, consultas DNF y paquetes."""

from core.repositories.dnf_query import (
    DnfGroup,
    DnfGroupDetails,
    DnfPackage,
    DnfQuery,
    DnfQueryError,
    DnfRepository,
    DnfUnavailableError,
)
from core.repositories.manager import RepositoryManager
from core.repositories.package_checker import (
    invalid_package_names,
    split_package_names,
    validate_product_name,
)

__all__ = [
    "DnfGroup",
    "DnfGroupDetails",
    "DnfPackage",
    "DnfQuery",
    "DnfQueryError",
    "DnfRepository",
    "DnfUnavailableError",
    "RepositoryManager",
    "invalid_package_names",
    "split_package_names",
    "validate_product_name",
]
