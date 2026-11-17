"""Paso 3: software (app kiosco, paquetes y multiventana)."""

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
    QVBoxLayout,
    QWidget,
)
from core.desktops.environments import get_desktop_environment, list_desktop_environments

HELP = """
<p><b>Seleccion de software</b></p>
<p>La aplicacion principal puede ser Chromium, Firefox o una aplicacion local
(binario, script, carpeta o RPM). En el modo multiventana, Sway reemplaza a Cage
y reparte la app principal y la segunda aplicacion en dos espacios de trabajo.</p>
<p>Los paquetes adicionales deben existir en Fedora 44 y se validan antes de
compilar. Los grupos comps (por ejemplo <code>@office</code>) se validan por
separado y se aplican con el motor Fedora Desktop; el motor Kiosco no los
instala. En modo Simple solo se muestran la aplicacion principal y
su URL; el resto de las opciones tecnicas queda en modo Avanzado.</p>
<p>Con el motor Fedora Desktop se elige el escritorio (GNOME, KDE Plasma o
Xfce) y la cuenta de escritorio; con el motor Kiosco se mantiene el kiosco con
Cage/Sway y <code>kioskuser</code>.</p>
<p>La administracion del equipo se realiza por SSH: Sway no incluye barras ni
terminal. <b>Alt+9</b> abre el configurador de red WiFi.</p>
"""


class SoftwareTabMixin:
    """Paso 3: software (app kiosco, paquetes y multiventana) (mixin de KioskBuilderGUI)."""

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
        desktop_layout.addWidget(self.lbl_desktop_env_description)
        desktop_layout.addWidget(self.combo_desktop_env)
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

        self.txt_extra_packages = QLineEdit()
        self.txt_extra_packages.setPlaceholderText(
            "ej: htop git tmux (separados por espacio, deben existir en Fedora 44)"
        )

        self.txt_extra_groups = QLineEdit()
        self.txt_extra_groups.setPlaceholderText(
            "ej: @office @multimedia (grupos comps del motor Desktop)"
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
        app_layout.addRow("Paquetes adicionales (dnf):", self.txt_extra_packages)
        app_layout.addRow("Grupos de paquetes (dnf):", self.txt_extra_groups)
        app_layout.addRow(self.check_allow_unsigned_rpms)
        app_layout.addRow(self.check_restart)
        app_layout.addRow(self.check_no_sandbox)
        app_hint = QLabel(
            "<i>Para apps locales en Python se detectan PySide6/PyQt y se "
            "inyectan las dependencias Qt del sistema.</i>"
        )
        app_hint.setWordWrap(True)
        app_layout.addRow("", app_hint)

        layout.addWidget(group_app)

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

        layout.addWidget(group_multi)

        self._register_advanced(group_env)
        self._register_advanced(self.txt_extra_packages, app_layout)
        self._register_advanced(self.txt_extra_groups, app_layout)
        self._register_advanced(self.check_allow_unsigned_rpms)
        self._register_advanced(self.check_restart)
        self._register_advanced(self.check_no_sandbox)
        self._register_advanced(group_multi)

        add_page(
            self,
            "step3",
            tab,
            "Selección de software",
            "Aplicacion principal, segunda aplicacion y paquetes adicionales.",
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
        if not visible:
            return
        key = str(getattr(self, "_desktop_environment", "gnome") or "gnome")
        index = self.combo_desktop_env.findData(key)
        if index < 0:
            index = 0
            key = str(self.combo_desktop_env.itemData(0) or "gnome")
        self.combo_desktop_env.setCurrentIndex(index)
        environment = get_desktop_environment(key)
        self.lbl_desktop_env_description.setText(
            f"{environment['name']} · {environment['session_manager']} · "
            f"sesion {environment['session_type']}"
        )

    def _on_desktop_environment_changed(self, *_args):
        key = str(self.combo_desktop_env.currentData() or "gnome")
        self._desktop_environment = key

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
