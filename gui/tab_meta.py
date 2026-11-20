"""Paso 1: identidad y metadatos de la ISO."""

from core.projects.catalog import get_project_template, list_project_types
from gui.components import prepare_combo
from gui.layouts import add_page
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QGroupBox, QLabel, QLineEdit, QVBoxLayout, QWidget,
)

HELP = """
<p><b>Identidad del sistema</b></p>
<p>Define el nombre de la imagen, el producto que identificará al sistema
instalado y los datos de publicación. La identidad se conserva en los
metadatos y en los componentes del sistema que correspondan.</p>
<p>La distribución elegida define el motor de la imagen: <code>kiosk</code>
para un equipo dedicado, o uno de los perfiles Desktop (<code>oficina</code>,
<code>web</code>, <code>gaming</code>, <code>security_lab</code> o
<code>custom</code>) que usan el motor Fedora Desktop.</p>
<p>El motor Kiosco arranca directamente como Live, sin LightDM ni contraseña.
Los perfiles Fedora Desktop conservan una contraseña inicial para el usuario
de escritorio.</p>
<p>En modo Simple se ocultan las opciones técnicas de distribución base y
modo de arranque. Las opciones exclusivas de Kiosco se muestran en una página
independiente cuando el perfil activo corresponde a ese motor.</p>
"""


class MetaTabMixin:
    """Paso 1: identidad y metadatos de la ISO (mixin de KioskBuilderGUI)."""

    def init_tab_meta(self):
        tab = QWidget()
        page_layout = QVBoxLayout(tab)

        group_identity = QGroupBox("Identidad de la distribución")
        identity = QFormLayout(group_identity)
        identity.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.txt_name = QLineEdit("TallerArgOS-kiosk")
        self.txt_name.setPlaceholderText("Nombre identificador de la ISO")
        self.txt_product_name = QLineEdit("TallerArgOS Fedora Kiosk")
        self.txt_product_name.setToolTip(
            "Nombre del producto que muestra el instalador (Anaconda) y el "
            "sistema instalado. Dejalo vacio para mantener la identidad Fedora Linux."
        )
        self.txt_version = QLineEdit("1.0.0")
        self.txt_dev = QLineEdit("Sergio")
        identity.addRow("Nombre de la ISO:", self.txt_name)
        identity.addRow("Nombre del producto:", self.txt_product_name)
        identity.addRow("Versión:", self.txt_version)
        identity.addRow("Creador / Taller:", self.txt_dev)

        group_platform = QGroupBox("Plataforma y arranque")
        platform = QFormLayout(group_platform)
        self.combo_project_type = QComboBox()
        prepare_combo(self.combo_project_type, 22)
        self.combo_project_type.setToolTip(
            "Define el objetivo de la distribución y el motor de construcción."
        )
        self._password_label = None
        for key, name, tagline in list_project_types():
            self.combo_project_type.addItem(f"{name} — {tagline}", key)
        self.combo_project_type.currentIndexChanged.connect(self._on_project_type_changed)

        self.combo_base = QComboBox()
        self.combo_base.addItem("Fedora 44 (repos estáticos)", "44")
        self.combo_boot = QComboBox()
        self.combo_boot.addItem("Dual (UEFI + BIOS)", "dual")
        self.combo_boot.addItem("Solo UEFI", "uefi")
        self.combo_boot.setToolTip(
            "La imagen híbrida mantiene compatibilidad BIOS; esta opción controla "
            "la inclusión del stack EFI."
        )
        platform.addRow("Tipo de distribución:", self.combo_project_type)
        platform.addRow("Distribución base:", self.combo_base)
        platform.addRow("Modo de arranque:", self.combo_boot)

        group_account = QGroupBox("Cuenta de escritorio")
        account = QFormLayout(group_account)
        self.txt_desktop_user = QLineEdit(
            str(getattr(self, "_desktop_user", "fedora") or "fedora")
        )
        self.txt_desktop_user.setToolTip(
            "Usuario de la cuenta de escritorio. Solo aplica al motor Fedora Desktop; "
            "el motor Kiosco utiliza kioskuser."
        )
        self.txt_desktop_user.textChanged.connect(self._on_desktop_user_changed)
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setPlaceholderText(
            "Solo para Fedora Desktop; no se usa en el motor Kiosco"
        )
        self.txt_password.setToolTip(
            "Solo se aplica al usuario de escritorio en el motor Fedora Desktop."
        )
        account.addRow("Usuario:", self.txt_desktop_user)
        account.addRow("Contraseña inicial:", self.txt_password)
        self._password_label = account.labelForField(self.txt_password)

        self.meta_hint = QLabel(
            "Motor Kiosco: usuario técnico kioskuser, inicio automático sin contraseña. "
            "Motor Fedora Desktop: cuenta de escritorio con contraseña inicial."
        )
        self.meta_hint.setObjectName("inlineHint")
        self.meta_hint.setWordWrap(True)

        page_layout.addWidget(group_identity)
        page_layout.addWidget(group_platform)
        page_layout.addWidget(group_account)
        page_layout.addWidget(self.meta_hint)
        self.group_desktop_account = group_account
        page_layout.addStretch(1)

        self._register_advanced(self.combo_base, platform)
        self._register_advanced(self.combo_boot, platform)
        self._on_project_type_changed()
        add_page(
            self, "step1", tab, "Identidad del sistema",
            "Definí el producto, el perfil de distribución y la cuenta de usuario.",
            HELP, step=1,
        )

    def _on_project_type_changed(self, *_args):
        key = str(self.combo_project_type.currentData() or "custom")
        self._project_type = key
        self._build_engine = get_project_template(key)["engine"]
        refresh = getattr(self, "refresh_desktop_environment_fields", None)
        if callable(refresh):
            refresh()
        mode_refresh = getattr(self, "refresh_project_mode_fields", None)
        if callable(mode_refresh):
            mode_refresh()
        if hasattr(self, "txt_password"):
            is_kiosk = key == "kiosk"
            self.txt_password.setVisible(not is_kiosk)
            if self._password_label is not None:
                self._password_label.setVisible(not is_kiosk)
            if hasattr(self, "meta_hint"):
                self.meta_hint.setText(
                    "Motor Kiosco: inicio automático tipo Live, sin LightDM ni "
                    "contraseña. Motor Fedora Desktop: usuario de escritorio con "
                    "contraseña inicial."
                )

    def _on_desktop_user_changed(self, *_args):
        value = self.txt_desktop_user.text().strip()
        self._desktop_user = value or "fedora"
