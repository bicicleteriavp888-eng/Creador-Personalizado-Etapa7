"""Paso 2: apariencia (splash de Plymouth y resolución)."""

from core.builder import MAX_PLYMOUTH_BYTES
from gui.components import configure_image_preview
from gui.images import ImageField
from gui.layouts import add_page
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QVBoxLayout, QWidget,
)

HELP = """
<p><b>Apariencia y personalización</b></p>
<p>La imagen seleccionada se muestra en el menú inicial de arranque (BIOS/Legacy
y UEFI) y durante la carga del sistema mediante Plymouth. Si no elegís una
imagen se conserva el tema del sistema. Se convierte a PNG y se limita a 4 MiB.</p>
<p>La resolución se aplica con <code>wlr-randr</code> dentro de la sesión Cage o
Sway. Si el monitor no soporta el modo elegido, se usa el preferido por el hardware.</p>
"""


class AestheticTabMixin:
    """Paso 2: estética (splash y resolución) (mixin de KioskBuilderGUI)."""

    def init_tab_aesthetic(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        group_splash = QGroupBox("Imagen de inicio · Plymouth")
        splash_layout = QVBoxLayout(group_splash)
        self.plymouth_preview = QLabel("Sin imagen · tema del sistema")
        self.plymouth_preview.setObjectName("imagePreview")
        configure_image_preview(self.plymouth_preview)
        splash_layout.addWidget(self.plymouth_preview, 0)

        self.btn_plymouth = QPushButton("Seleccionar imagen…")
        self.btn_plymouth.setToolTip(
            "Selecciona la imagen que se mostrará en el menú de arranque y durante Plymouth."
        )
        self.lbl_plymouth = QLabel("Por defecto · tema del sistema")
        self.lbl_plymouth.setWordWrap(True)
        self.lbl_plymouth.setObjectName("inlineHint")
        self.btn_plymouth_clear = QPushButton("Quitar imagen")
        self.plymouth_field = ImageField(
            self, self.plymouth_preview, self.lbl_plymouth,
            "Seleccionar imagen de boot splash", "plymouth-splash.png",
            MAX_PLYMOUTH_BYTES, "4 MiB", "Sin imagen · tema del sistema",
            "Por defecto · tema del sistema",
        )
        self.btn_plymouth.clicked.connect(self.plymouth_field.select)
        self.btn_plymouth_clear.clicked.connect(self.plymouth_field.clear)
        actions = QHBoxLayout()
        actions.addWidget(self.btn_plymouth)
        actions.addWidget(self.btn_plymouth_clear)
        actions.addStretch(1)
        splash_layout.addLayout(actions)
        splash_layout.addWidget(self.lbl_plymouth)
        hint = QLabel(
            "PNG, JPG, WebP o BMP. Se convierte y optimiza a PNG (máximo 4 MiB). "
            "Para el menú BIOS/Legacy se recomienda una imagen de 640 × 480."
        )
        hint.setObjectName("inlineHint")
        hint.setWordWrap(True)
        splash_layout.addWidget(hint)

        group_display = QGroupBox("Resolución de pantalla")
        display = QFormLayout(group_display)
        self.combo_res = QComboBox()
        self.combo_res.addItem("Autodetectar (recomendado)", "auto")
        for resolution in ("1360x768", "1920x1080", "1280x720"):
            self.combo_res.addItem(resolution, resolution)
        display.addRow("Resolución:", self.combo_res)
        resolution_hint = QLabel(
            "Se configura mediante wlr-randr dentro de Cage o Sway. Si el modo "
            "no está disponible, se utiliza la resolución preferida por el monitor."
        )
        resolution_hint.setObjectName("inlineHint")
        resolution_hint.setWordWrap(True)
        display.addRow("", resolution_hint)

        layout.addWidget(group_splash)
        layout.addWidget(group_display)
        layout.addStretch(1)
        self._register_advanced(self.combo_res, display)
        add_page(
            self, "step2", tab, "Apariencia y personalización",
            "Personalizá la pantalla de inicio y el comportamiento de pantalla.",
            HELP, step=2,
        )
