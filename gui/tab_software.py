"""Paso 3: catálogo de software y selección del escritorio."""

from gui.components import prepare_combo
from gui.layouts import add_page
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QInputDialog,
    QVBoxLayout,
    QWidget,
)
from core.hardware.scanner import scan_hardware, export_hardware_profile, load_hardware_profile
from core.desktops.environments import (
    get_desktop_environment,
    list_desktop_environments,
    supported_display_servers,
)

HELP = """
<p><b>Software de la distribución</b></p>
<p>El paso 3 concentra el acceso al catálogo único de software Fedora. Desde
el gestor se consultan repositorios, paquetes, grupos Comps y dependencias;
la selección se comparte con el proyecto y con las herramientas.</p>
<p>En el motor Fedora Desktop se elige GNOME, KDE Plasma o Xfce. El selector
muestra Wayland o X11 y deshabilita las combinaciones que no están disponibles
en Fedora 44 para ese escritorio: GNOME y Plasma usan Wayland; Xfce utiliza X11.</p>
<p>Las opciones de aplicación, Cage/Sway y multiventana del motor Kiosco
se administran en la página independiente <b>Configuración Kiosco</b>. La
administración del equipo se realiza por SSH; <b>Alt+9</b> abre el configurador
 de red WiFi.</p>
"""


class SoftwareTabMixin:
    """Paso 3: catálogo de software y selección del escritorio."""

    def init_tab_software(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        group_env = QGroupBox("Entorno Grafico Objetivo")
        env_layout = QVBoxLayout(group_env)
        env_layout.addWidget(QLabel("OK Servidor grafico: Wayland"))
        self.lbl_compositor = QLabel(
            "OK Compositor de kiosco: Cage (pantalla completa, sin barras)"
        )
        self.lbl_compositor.setWordWrap(True)
        env_layout.addWidget(self.lbl_compositor)
        layout.addWidget(group_env)
        self.group_env = group_env

        # Escritorio de la distribucion: solo se muestra con el motor Desktop.
        group_desktop = QGroupBox("Escritorio de la distribución")
        desktop_layout = QVBoxLayout(group_desktop)
        self.lbl_desktop_env_description = QLabel()
        self.lbl_desktop_env_description.setWordWrap(True)
        self.combo_desktop_env = QComboBox()
        prepare_combo(self.combo_desktop_env, 18)
        self.combo_desktop_env.setToolTip(
            "Gestor de sesión y tipo de sesion de la distribucion de escritorio."
        )
        for key, name, manager in list_desktop_environments():
            self.combo_desktop_env.addItem(f"{name} · {manager}", key)
        self.combo_desktop_env.currentIndexChanged.connect(
            self._on_desktop_environment_changed
        )
        self.combo_display_server = QComboBox()
        prepare_combo(self.combo_display_server, 18)
        self.combo_display_server.setToolTip(
            "Servidor gráfico de la sesión. Las opciones dependen del escritorio "
            "y de los paquetes disponibles en Fedora 44."
        )
        self.combo_display_server.currentIndexChanged.connect(
            self._on_display_server_changed
        )
        desktop_layout.addWidget(self.lbl_desktop_env_description)
        desktop_layout.addWidget(self.combo_desktop_env)
        desktop_layout.addWidget(QLabel("Servidor gráfico de la sesión:"))
        desktop_layout.addWidget(self.combo_display_server)
        layout.addWidget(group_desktop)
        self.group_desktop_env = group_desktop
        self.refresh_desktop_environment_fields()

        group_app = QGroupBox("Aplicacion en Kiosco")
        app_layout = QFormLayout(group_app)

        self.combo_default_app = QComboBox()
        self.combo_default_app.addItem("Chromium (kiosk Wayland)", "chromium")
        self.combo_default_app.addItem("Firefox (kiosk)", "firefox")
        self.combo_default_app.addItem(
            "Firefox (kiosk en espanol es-AR)", "firefox-es"
        )
        self.combo_default_app.addItem(
            "Aplicacion local (binario, script o RPM)", "custom"
        )
        self.combo_default_app.currentIndexChanged.connect(self.update_app_fields)

        self.txt_url = QLineEdit("http://localhost")
        self.txt_url.setPlaceholderText("URL que abrira el navegador en kiosco")

        self.btn_custom_app = QPushButton("Archivo / RPM...")
        self.btn_custom_app.setToolTip(
            "Selecciona el ejecutable, el script o el paquete .rpm de la app. "
            "Si eliges un .rpm, se instala dentro de la imagen y el kiosco "
            "arranca con el ejecutable que trae el paquete."
        )
        self.btn_custom_app.clicked.connect(self.select_app_file)
        self.btn_custom_dir = QPushButton("Carpeta...")
        self.btn_custom_dir.clicked.connect(self.select_app_dir)

        custom_row = QHBoxLayout()
        custom_row.addWidget(self.btn_custom_app)
        custom_row.addWidget(self.btn_custom_dir)

        self.lbl_custom_app = QLabel("No seleccionado")
        self.lbl_custom_app.setWordWrap(True)

        # La selección real se administra desde el gestor Fedora compartido.
        # Estos campos son una vista resumida compatible con la configuración
        # histórica del proyecto; no son un segundo selector manual.
        self.txt_extra_packages = QLineEdit()
        self.txt_extra_packages.setPlaceholderText(
            "Sin paquetes adicionales seleccionados"
        )
        self.txt_extra_packages.setReadOnly(True)
        self.txt_extra_groups = QLineEdit()
        self.txt_extra_groups.setPlaceholderText(
            "Sin grupos Comps seleccionados"
        )
        self.txt_extra_groups.setReadOnly(True)
        self.btn_open_software_manager = QPushButton(
            "Abrir gestor de software Fedora…"
        )
        self.btn_open_software_manager.setToolTip(
            "Abrir el catálogo único de repositorios, paquetes, grupos Comps "
            "y resolución de dependencias."
        )
        self.btn_open_software_manager.clicked.connect(
            lambda: self._navigate("custom_distro", validate=False)
        )
        self.txt_extra_groups.setToolTip(
            "Grupos de paquetes Fedora (comps). Se validan como @grupo y se "
            "aplican con el motor Fedora Desktop; el motor Kiosco no los instala."
        )

        self.check_allow_unsigned_rpms = QCheckBox(
            "Permitir instalar RPM sin firma digital (bajo mi responsabilidad)"
        )
        self.check_allow_unsigned_rpms.setChecked(False)
        self.check_allow_unsigned_rpms.setToolTip(
            "Solo acepta RPM sin firma cuyo contenido pase la comprobación de digests. "
            "Las firmas inválidas, claves desconocidas y paquetes corruptos siguen rechazándose."
        )
        self.check_allow_unsigned_rpms.toggled.connect(
            self.confirm_unsigned_rpm_policy
        )

        self.check_restart = QCheckBox(
            "Reiniciar la app automaticamente ante fallos (Restart=always)"
        )
        self.check_restart.setChecked(True)

        self.check_no_sandbox = QCheckBox(
            "Deshabilitar sandbox de Chromium (menos seguro)"
        )
        self.check_no_sandbox.setChecked(False)
        self.check_no_sandbox.setToolTip(
            "Por defecto Chromium usa su sandbox. Activa esta opcion solo si "
            "el navegador no arranca en el hardware destino."
        )

        app_layout.addRow("Aplicacion Principal:", self.combo_default_app)
        app_layout.addRow("URL de inicio:", self.txt_url)
        app_layout.addRow("Ruta de app propia:", custom_row)
        app_layout.addRow("", self.lbl_custom_app)
        app_layout.addRow(self.check_allow_unsigned_rpms)
        app_layout.addRow(self.check_restart)
        app_layout.addRow(self.check_no_sandbox)
        app_hint = QLabel(
            "<i>Para apps locales en Python se detectan PySide6/PyQt y se "
            "inyectan las dependencias Qt del sistema.</i>"
        )
        app_hint.setWordWrap(True)
        app_layout.addRow("", app_hint)

        # La configuración de aplicaciones Kiosco vive en una página separada.
        # Así el paso 3 queda dedicado al gestor Fedora y al escritorio Desktop.
        self.group_kiosk_app = group_app

        group_software = QGroupBox("Software de la distribución")
        software_layout = QFormLayout(group_software)
        software_hint = QLabel(
            "Elegí paquetes, grupos y dependencias desde el gestor único de "
            "software Fedora. La selección se comparte con el proyecto y con "
            "las herramientas."
        )
        software_hint.setWordWrap(True)
        software_layout.addRow("", software_hint)
        software_layout.addRow("Paquetes seleccionados:", self.txt_extra_packages)
        software_layout.addRow("Grupos Comps seleccionados:", self.txt_extra_groups)
        software_layout.addRow("", self.btn_open_software_manager)
        layout.addWidget(group_software)
        self.group_software = group_software

        # Diagnóstico del host y perfiles portables: el escáner es de solo
        # lectura y nunca instala paquetes ni habilita repositorios.
        group_hardware = QGroupBox("Diagnóstico y perfiles de hardware")
        hardware_layout = QVBoxLayout(group_hardware)
        hardware_hint = QLabel(
            "Analiza PCI/USB del equipo de compilación (lspci -nnk y lsusb), "
            "sugiere paquetes Fedora y permite guardar/cargar recetas de hardware."
        )
        hardware_hint.setWordWrap(True)
        hardware_layout.addWidget(hardware_hint)
        hardware_actions = QHBoxLayout()
        self.btn_scan_hardware = QPushButton("Analizar hardware del equipo")
        self.btn_scan_hardware.clicked.connect(self.scan_host_hardware)
        self.btn_export_hardware = QPushButton("Exportar perfil…")
        self.btn_export_hardware.clicked.connect(self.export_host_hardware_profile)
        self.btn_import_hardware = QPushButton("Cargar perfil…")
        self.btn_import_hardware.clicked.connect(self.import_host_hardware_profile)
        hardware_actions.addWidget(self.btn_scan_hardware)
        hardware_actions.addWidget(self.btn_export_hardware)
        hardware_actions.addWidget(self.btn_import_hardware)
        hardware_layout.addLayout(hardware_actions)
        self.lbl_hardware_scan = QLabel("Todavía no se analizó el hardware.")
        self.lbl_hardware_scan.setWordWrap(True)
        hardware_layout.addWidget(self.lbl_hardware_scan)
        layout.addWidget(group_hardware)
        self._last_hardware_scan = None

        group_multi = QGroupBox("Segunda aplicacion / Multiventana (Sway)")
        multi_layout = QFormLayout(group_multi)

        self.check_multi_app = QCheckBox(
            "Habilitar segunda aplicacion con cambio de ventana (Sway)"
        )
        self.check_multi_app.setChecked(True)
        self.check_multi_app.setToolTip(
            "Sway reemplaza a Cage y ejecuta la app principal en el workspace 1 "
            "y la segunda app en el workspace 2. Se cambia con Super+1 / "
            "Super+2 / Super+Tab (o Alt+1 / Alt+2 / Alt+Tab). Con Alt+9 se "
            "abre el configurador de red WiFi."
        )
        self.check_multi_app.toggled.connect(self.update_app_fields)

        self.combo_app2 = QComboBox()
        self.combo_app2.addItem("Chromium (kiosk Wayland)", "chromium")
        self.combo_app2.addItem("Firefox (kiosk)", "firefox")
        self.combo_app2.addItem(
            "Firefox (kiosk en espanol es-AR)", "firefox-es"
        )
        self.combo_app2.addItem("Comando personalizado", "custom")
        self.combo_app2.addItem(
            "Archivo local (binario, script o RPM)", "local"
        )
        # Por defecto la segunda aplicacion es Firefox en espanol.
        self.combo_app2.setCurrentIndex(self.combo_app2.findData("firefox-es"))
        self.combo_app2.currentIndexChanged.connect(self.update_app2_fields)
        self.app2_local_path = ""

        self.txt_url2 = QLineEdit("http://localhost")
        self.txt_url2.setPlaceholderText("URL que abrira la segunda aplicacion")
        self.txt_url2.setToolTip(
            "URL de la segunda app cuando es Chromium o Firefox."
        )

        self.txt_cmd2 = QLineEdit()
        self.txt_cmd2.setPlaceholderText(
            "ej: /usr/bin/htop o chromium --kiosk http://localhost"
        )
        self.txt_cmd2.setToolTip(
            "Comando simple que debe existir dentro de la imagen. Si el "
            "programa no viene en Fedora, agrega su paquete en "
            "'Paquetes adicionales'."
        )
        self.btn_app2_file = QPushButton("Archivo / RPM...")
        self.btn_app2_file.setToolTip(
            "Copia a la imagen el binario, script o RPM seleccionado y lo usa "
            "como segunda aplicacion."
        )
        self.btn_app2_file.clicked.connect(self.select_app2_local_file)

        self.lbl_app2_local = QLabel("No seleccionado")
        self.lbl_app2_local.setWordWrap(True)

        local2_row = QHBoxLayout()
        local2_row.addWidget(self.btn_app2_file)
        local2_row.addWidget(self.lbl_app2_local, 1)

        self.lbl_app2_hint = QLabel(
            "<i>La app principal va al workspace 1 y la segunda al 2. "
            "Atajos: Super+1 / Super+2 / Super+Tab (Alt+1 / Alt+2 / Alt+Tab "
            "tambien); Alt+9 abre el configurador de red WiFi. 'Archivo "
            "local' copia el programa (o instala el RPM) en la imagen; en "
            "'Comando personalizado' el programa debe venir en un paquete "
            "instalado. Sway no tiene barras ni terminal: la administracion "
            "sigue siendo por SSH.</i>"
        )
        self.lbl_app2_hint.setWordWrap(True)

        multi_layout.addRow(self.check_multi_app)
        multi_layout.addRow("Segunda aplicacion:", self.combo_app2)
        multi_layout.addRow("URL de inicio:", self.txt_url2)
        multi_layout.addRow("Comando:", self.txt_cmd2)
        multi_layout.addRow("Archivo local:", local2_row)
        multi_layout.addRow("", self.lbl_app2_hint)

        # Página opcional y exclusiva del motor Kiosco. No forma parte del
        # recorrido Desktop ni modifica el paso 3 solicitado para Fedora.
        kiosk_page = QWidget()
        kiosk_layout = QVBoxLayout(kiosk_page)
        kiosk_layout.addWidget(group_app)
        kiosk_layout.addWidget(group_multi)
        kiosk_layout.addStretch(1)
        add_page(
            self, "kiosk_config", kiosk_page, "Configuración Kiosco",
            "Definí la aplicación de inicio y, si lo necesitás, el modo multiventana. "
            "Estas opciones solo pertenecen al motor Kiosco.",
            "<p><b>Configuración exclusiva de Kiosco</b></p>"
            "<p>Elegí Chromium, Firefox o una aplicación propia. La segunda "
            "aplicación y el cambio de ventana se ejecutan mediante Sway.</p>",
            step=None,
        )

        self._register_advanced(group_env)
        self._register_advanced(self.txt_extra_packages, software_layout)
        self._register_advanced(self.txt_extra_groups, software_layout)
        self.group_multi_app = group_multi
        self._register_advanced(group_multi)
        self._register_advanced(self.check_allow_unsigned_rpms)
        self._register_advanced(self.check_no_sandbox)
        self.refresh_desktop_environment_fields()

        add_page(
            self,
            "step3",
            tab,
            "Selección de software",
            "Selección de escritorio y servidor gráfico, más el catálogo único de software Fedora.",
            HELP,
            step=3,
        )

        self.update_app_fields()

    def confirm_unsigned_rpm_policy(self, checked):
        """Exige una confirmación adicional al habilitar RPM sin firma."""
        if not checked:
            return
        answer = QMessageBox.warning(
            self,
            "Aceptar RPM sin firma",
            "Los paquetes RPM sin firma pueden haber sido modificados o contener "
            "software malicioso. Solo continúa si confías en el archivo y en su "
            "origen.\n\nSe seguirán rechazando firmas inválidas, claves desconocidas "
            "y paquetes con digests incorrectos.\n\n¿Asumes la responsabilidad?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            self.check_allow_unsigned_rpms.blockSignals(True)
            self.check_allow_unsigned_rpms.setChecked(False)
            self.check_allow_unsigned_rpms.blockSignals(False)

    def update_app_fields(self, *args):
        is_custom = self.combo_default_app.currentData() == "custom"
        self.btn_custom_app.setEnabled(is_custom)
        self.btn_custom_dir.setEnabled(is_custom)
        self.lbl_custom_app.setEnabled(is_custom)
        self.txt_url.setEnabled(not is_custom)

        if self.check_multi_app.isChecked():
            self.lbl_compositor.setText(
                "OK Compositor de kiosco: Sway (dos apps en workspaces 1 y 2; "
                "cambio con Super+1 / Super+2 / Super+Tab; Alt+9 red WiFi)"
            )
        else:
            self.lbl_compositor.setText(
                "OK Compositor de kiosco: Cage (pantalla completa, sin barras)"
            )
        self.update_app2_fields()

    def update_app2_fields(self, *args):
        enabled = self.check_multi_app.isChecked()
        mode = self.combo_app2.currentData()
        self.combo_app2.setEnabled(enabled)
        self.txt_url2.setEnabled(
            enabled and mode in ("chromium", "firefox", "firefox-es")
        )
        self.txt_cmd2.setEnabled(enabled and mode == "custom")
        self.btn_app2_file.setEnabled(enabled and mode == "local")
        self.lbl_app2_local.setEnabled(enabled and mode == "local")
        self.lbl_app2_hint.setEnabled(enabled)

    # -- Escritorio (motor Fedora Desktop) -------------------------------------

    def refresh_desktop_environment_fields(self):
        """Muestra u oculta el selector de escritorio segun el motor."""
        engine = self._selected_build_engine()
        visible = engine == "desktop"
        # Esta funcion tambien se invoca desde la pestaña Meta, que se crea
        # antes que la pestaña Software en KioskBuilderGUI._init_pages().
        # Durante esa primera llamada los widgets de escritorio aun no existen.
        if not hasattr(self, "group_desktop_env"):
            return
        self.group_desktop_env.setVisible(visible)
        advanced = getattr(self, "ui_mode", "advanced") == "advanced"
        if hasattr(self, "group_env"):
            self.group_env.setVisible((not visible) and advanced)
        if hasattr(self, "group_multi_app"):
            self.group_multi_app.setVisible((not visible) and advanced)
        if hasattr(self, "group_kiosk_app"):
            self.group_kiosk_app.setVisible(not visible)
        if hasattr(self, "_nav_buttons") and "kiosk_config" in self._nav_buttons:
            self._nav_buttons["kiosk_config"].setVisible(not visible)
        if not visible:
            if getattr(self, "_current_key", "") == "kiosk_config":
                self._navigate("step3", validate=False)
            return
        key = str(getattr(self, "_desktop_environment", "gnome") or "gnome")
        index = self.combo_desktop_env.findData(key)
        if index < 0:
            index = 0
            key = str(self.combo_desktop_env.itemData(0) or "gnome")
        self.combo_desktop_env.blockSignals(True)
        self.combo_desktop_env.setCurrentIndex(index)
        self.combo_desktop_env.blockSignals(False)
        environment = get_desktop_environment(key)
        current_server = str(
            getattr(self, "_display_server", environment["session_type"]) or environment["session_type"]
        ).lower()
        options = supported_display_servers(key)
        self.combo_display_server.blockSignals(True)
        self.combo_display_server.clear()
        for server, label in (("wayland", "Wayland"), ("x11", "X11")):
            self.combo_display_server.addItem(label, server)
            item = self.combo_display_server.model().item(
                self.combo_display_server.count() - 1
            )
            if server not in options:
                item.setEnabled(False)
                item.setToolTip(
                    f"{label} no está disponible para {environment['name']} "
                    "en los repositorios Fedora 44 configurados."
                )
        if current_server not in options:
            current_server = environment["session_type"]
        self.combo_display_server.setCurrentIndex(
            max(0, self.combo_display_server.findData(current_server))
        )
        self.combo_display_server.blockSignals(False)
        self._display_server = current_server
        self.lbl_desktop_env_description.setText(
            f"{environment['name']} · {environment['session_manager']} · "
            f"sesión {current_server.upper()}"
        )

    def _on_desktop_environment_changed(self, *_args):
        key = str(self.combo_desktop_env.currentData() or "gnome")
        self._desktop_environment = key
        self.refresh_desktop_environment_fields()

    def _on_display_server_changed(self, *_args):
        server = str(self.combo_display_server.currentData() or "").lower()
        if server:
            self._display_server = server
            self.refresh_desktop_environment_description()

    def refresh_desktop_environment_description(self):
        key = str(getattr(self, "_desktop_environment", "gnome") or "gnome")
        environment = get_desktop_environment(key)
        server = str(getattr(self, "_display_server", environment["session_type"]))
        self.lbl_desktop_env_description.setText(
            f"{environment['name']} · {environment['session_manager']} · sesión {server.upper()}"
        )

    def select_app2_local_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar binario, script o RPM de la segunda aplicacion",
            "",
            "Ejecutables y paquetes (*.rpm);;Todos los archivos (*)",
        )
        if path:
            self.app2_local_path = path
            self.lbl_app2_local.setText(path)

    def select_app_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar ejecutable, script o paquete RPM",
            "",
            "Ejecutables y paquetes (*.rpm);;Todos los archivos (*)",
        )
        if path:
            self.custom_app_path = path
            self.lbl_custom_app.setText(path)

    def select_app_dir(self):
        path = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta de la aplicacion"
        )
        if path:
            self.custom_app_path = path
            self.lbl_custom_app.setText(path)


    def scan_host_hardware(self):
        """Analiza PCI/USB y ofrece agregar solo paquetes base de Fedora."""
        try:
            report = scan_hardware()
            self._last_hardware_scan = report
            recommendations = report.get("recommendations", [])
            base = [item["package"] for item in recommendations
                    if not item.get("requires_external_repo")]
            manual = [item["package"] for item in recommendations
                      if item.get("requires_external_repo")]
            self.lbl_hardware_scan.setText(
                f"PCI: {len(report.get('pci_devices', []))} · USB: "
                f"{len(report.get('usb_devices', []))} · "
                f"Paquetes base sugeridos: {', '.join(base) or 'ninguno'} · "
                f"Controladores manuales: {', '.join(manual) or 'ninguno'}"
            )
            if base:
                reply = QMessageBox.question(
                    self, "Recomendaciones de hardware",
                    "Se detectaron estos paquetes base de Fedora:\n\n"
                    + ", ".join(base)
                    + "\n\n¿Querés agregarlos a la selección de software? "
                    "Los controladores externos no se agregarán automáticamente.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    current = [x for x in self.txt_extra_packages.text().split() if x]
                    merged = list(dict.fromkeys(current + base))
                    self.txt_extra_packages.setText(" ".join(merged))
            QMessageBox.information(
                self, "Diagnóstico de hardware",
                report.get("notice", "Análisis terminado.")
                + ("\n\nControladores de terceros: " + ", ".join(manual)
                   + ". Requieren revisión manual y repositorio externo."
                   if manual else "")
            )
        except Exception as exc:
            QMessageBox.warning(self, "Diagnóstico de hardware", str(exc))

    def export_host_hardware_profile(self):
        """Guarda selección y diagnóstico en un perfil JSON portable."""
        try:
            name, accepted = QInputDialog.getText(
                self, "Exportar perfil de hardware", "Nombre del perfil:"
            )
            if not accepted or not name.strip():
                return
            path, _ = QFileDialog.getSaveFileName(
                self, "Guardar perfil de hardware", name.strip().replace(" ", "-") + ".json",
                "Perfiles JSON (*.json)"
            )
            if not path:
                return
            report = self._last_hardware_scan or scan_hardware()
            selected = [x for x in self.txt_extra_packages.text().split() if x]
            resolution = self.combo_res.currentData() or "auto"
            export_hardware_profile(path, report, name, str(resolution), selected)
            QMessageBox.information(self, "Perfil exportado", f"Perfil guardado en:\n{path}")
        except Exception as exc:
            QMessageBox.warning(self, "Exportar perfil", str(exc))

    def import_host_hardware_profile(self):
        """Carga un perfil y fusiona paquetes validados con la selección actual."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Cargar perfil de hardware", "",
            "Perfiles JSON (*.json)"
        )
        if not path:
            return
        try:
            profile = load_hardware_profile(path)
            current = [x for x in self.txt_extra_packages.text().split() if x]
            merged = list(dict.fromkeys(current + profile.get("selected_packages", [])))
            self.txt_extra_packages.setText(" ".join(merged))
            resolution = str(profile.get("resolution") or "auto")
            for index in range(self.combo_res.count()):
                if self.combo_res.itemData(index) == resolution:
                    self.combo_res.setCurrentIndex(index)
                    break
            self.lbl_hardware_scan.setText(
                f"Perfil cargado: {profile.get('name', 'sin nombre')} · "
                f"{len(profile.get('selected_packages', []))} paquetes."
            )
        except Exception as exc:
            QMessageBox.warning(self, "Cargar perfil", str(exc))
