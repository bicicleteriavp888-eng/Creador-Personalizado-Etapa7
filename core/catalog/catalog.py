"""Gestor del catálogo de aplicaciones para Creador-kiosk 2.0."""

import json
import os


_PROJECT_CATALOG = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "catalog", "applications.json")
)
_SYSTEM_CATALOG = "/usr/share/creador-kiosk/catalog/applications.json"
CATALOG_PATH = _PROJECT_CATALOG if os.path.isfile(_PROJECT_CATALOG) else _SYSTEM_CATALOG


def load_catalog():
    """Carga el catálogo de aplicaciones desde el archivo JSON."""
    if not os.path.exists(CATALOG_PATH):
        return {"categories": [], "applications": []}
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_applications_by_category(category):
    """Devuelve las aplicaciones pertenecientes a una categoría."""
    cat_data = load_catalog()
    return [
        app for app in cat_data.get("applications", []) if app.get("category") == category
    ]


def find_application(app_id):
    """Busca una aplicación por su ID."""
    cat_data = load_catalog()
    for app in cat_data.get("applications", []):
        if app.get("id") == app_id:
            return app
    return None
