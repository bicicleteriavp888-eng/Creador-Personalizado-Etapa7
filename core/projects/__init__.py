"""Catálogo y validación de tipos de proyecto."""
from .catalog import PROJECT_TYPES, get_project_template, list_project_types, merge_packages

__all__ = ["PROJECT_TYPES", "get_project_template", "list_project_types", "merge_packages"]
