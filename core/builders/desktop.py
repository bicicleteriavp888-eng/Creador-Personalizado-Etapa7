"""Constructor de imágenes Fedora Desktop.

Reutiliza el ciclo de compilación probado de ``KioskISOBuilder`` (preflight,
directorios, espacio, ejecución de ``livecd-creator``, publicación e historial)
pero sustituye por completo la receta Kiosco. El Kickstart se genera con
``DesktopKickstartGenerator`` y no incluye componentes de kiosco.

La clase no modifica ``kiosk.ks`` ni los métodos de Cage, Sway, LightDM o
``kioskuser`` del motor Kiosco.
"""
from __future__ import annotations

import os

from core.builder import KioskISOBuilder
from core.constants import DEFAULT_MIRRORLIST
from core.desktops.kickstart import DesktopKickstartGenerator


class DesktopISOBuilder(KioskISOBuilder):
    """Constructor del motor Fedora Desktop con ciclo de build compartido."""

    engine = "desktop"

    def __init__(self, config):
        config = dict(config or {})
        config.setdefault("iso_name", "Fedora-Desktop")
        super().__init__(config)

        # El generador valida el entorno al construirse. Así un entorno
        # desconocido se rechaza antes de llegar a livecd-creator.
        self.desktop_generator = DesktopKickstartGenerator(self.config)
        self.desktop_environment = str(
            self.desktop_generator.config.get("desktop_environment") or "gnome"
        ).strip().lower()

        # Archivos propios para no mezclar ni sobrescribir la receta kiosco.
        self.ks_path = os.path.join(self.work_dir, "desktop.ks")
        self.log_path = os.path.join(self.work_dir, "desktop-build.log")

        # El motor Desktop admite CREADOR_MIRROR como nombre principal y
        # conserva KIOSK_MIRROR como compatibilidad con despliegues existentes.
        self.mirror = (
            os.environ.get("CREADOR_MIRROR")
            or os.environ.get("KIOSK_MIRROR")
            or ""
        ).rstrip("/")
        self.mirrorlist = (
            os.environ.get("CREADOR_MIRRORLIST")
            or os.environ.get("KIOSK_MIRRORLIST")
            or DEFAULT_MIRRORLIST
        ).rstrip("/")

    # -- Validación y receta -------------------------------------------------

    def _uses_local_rpm(self):
        """El motor Desktop no copia aplicaciones locales del kiosco."""
        return False

    def validate_configuration(self):
        """Valida la configuración Desktop antes de iniciar la compilación."""
        self.desktop_generator.validate()

    def _preflight(self):
        # Primero se valida la receta y la selección de software; después se
        # comprueban las herramientas del host y los repositorios.
        self.validate_configuration()
        super()._preflight()

    def _generate_kickstart(self, password_hash):
        self.log_signal.emit(
            "📝 Generando Kickstart Fedora Desktop "
            f"({self.desktop_generator.environment['name']})..."
        )
        self.desktop_generator.write(self.ks_path, password_hash)

    # -- Mensajes de salida --------------------------------------------------

    def _build_success_messages(self):
        environment = self.desktop_generator.environment
        username = self.desktop_generator.username
        messages = [
            f"🖥️ Escritorio: {environment['name']} · "
            f"gestor de sesión: {environment['session_manager']} · "
            f"usuario: {username}."
        ]
        if self.enable_ssh:
            messages.append(
                f"💡 Administración remota habilitada: ssh {username}@<ip> "
                "(usa clave pública si desactivaste contraseña)."
            )
        else:
            messages.append(
                "🔒 SSH permanece deshabilitado; habilitalo en la configuración "
                "si necesitás administración remota."
            )
        return messages
