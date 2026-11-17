"""Selección explícita del motor de construcción.

El motor Kiosco sigue siendo el predeterminado para configuraciones antiguas o
sin ``engine``. Los perfiles que declaran ``engine = "desktop"`` en el catálogo
de proyectos usan ``DesktopISOBuilder``, que comparte el ciclo de compilación
pero genera su propio Kickstart.
"""
from __future__ import annotations

from core.builder import KioskISOBuilder
from core.builders.desktop import DesktopISOBuilder
from core.projects.catalog import get_project_template

DEFAULT_BUILD_ENGINE = "kiosk"
SUPPORTED_BUILD_ENGINES = ("kiosk", "desktop")
BUILDERS = {
    "kiosk": KioskISOBuilder,
    "desktop": DesktopISOBuilder,
}


class BuildEngineError(ValueError):
    """Motor de construcción ausente, desconocido o inconsistente."""


def resolve_build_engine(config):
    """Resuelve ``kiosk`` o ``desktop`` sin cambiar el valor predeterminado.

    Prioridad:

    1. ``engine`` explícito en la configuración.
    2. ``engine`` del perfil indicado por ``project_type``.
    3. ``kiosk`` cuando no hay información de motor ni de proyecto.
    """
    config = dict(config or {})
    engine = str(config.get("engine") or "").strip().lower()

    if not engine:
        project_type = str(config.get("project_type") or "").strip().lower()
        if project_type:
            try:
                template = get_project_template(project_type)
            except ValueError as exc:
                raise BuildEngineError(str(exc)) from exc
            engine = str(template.get("engine") or DEFAULT_BUILD_ENGINE).strip().lower()
        else:
            engine = DEFAULT_BUILD_ENGINE

    if engine not in SUPPORTED_BUILD_ENGINES:
        raise BuildEngineError(
            f"Motor de construcción desconocido: {engine or '(vacío)'}. "
            f"Motores disponibles: {', '.join(SUPPORTED_BUILD_ENGINES)}."
        )
    return engine


def resolve_builder_class(config):
    """Devuelve la clase del constructor que corresponde a la configuración."""
    return BUILDERS[resolve_build_engine(config)]
