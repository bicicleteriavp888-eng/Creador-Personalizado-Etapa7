"""Seleccion, conversion y vista previa de imagenes para la ISO."""

import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QFileDialog, QMessageBox


class ImageField:
    """Seleccion, conversion y vista previa de una imagen para la ISO.

    Reune la logica que antes se duplicaba para el splash de Plymouth, el
    fondo del splash de Plymouth y el banner del instalador: elegir el
    archivo, convertirlo a un PNG que quepa en el Kickstart, mostrar la
    vista previa y limpiar la seleccion.
    """

    CACHE_DIR = "~/.cache/creador-kiosk"

    def __init__(
        self,
        owner,
        preview,
        label,
        dialog_title,
        cache_name,
        max_bytes,
        limit_label,
        empty_preview_text,
        default_label_text,
    ):
        self.owner = owner
        self.preview = preview
        self.label = label
        self.dialog_title = dialog_title
        self.cache_name = cache_name
        self.max_bytes = max_bytes
        self.limit_label = limit_label
        self.empty_preview_text = empty_preview_text
        self.default_label_text = default_label_text
        self.path = ""
        self.source_path = ""

    # -- Seleccion ----------------------------------------------------------

    def select(self):
        path, _ = QFileDialog.getOpenFileName(
            self.owner,
            self.dialog_title,
            "",
            "Imagenes (*.png *.jpg *.jpeg *.webp *.bmp);;Todos los archivos (*)",
        )
        if not path:
            return

        image = QImage(path)
        if image.isNull():
            QMessageBox.warning(
                self.owner,
                "Imagen no valida",
                "No se pudo leer la imagen. Usa PNG, JPG, WebP o BMP.",
            )
            return

        self.source_path = path
        already_ok = (
            path.lower().endswith(".png")
            and os.path.getsize(path) <= self.max_bytes
        )
        if already_ok:
            self.path = path
            self.update_display(converted=False)
            return

        prepared = self._prepare(image)
        if prepared is None:
            return
        self.path = prepared
        self.update_display(converted=True)

    def clear(self):
        cache = self.cache_path
        if os.path.isfile(cache):
            os.unlink(cache)
        self.path = ""
        self.source_path = ""
        self.update_display()

    def set_enabled(self, enabled):
        """Habilita o deshabilita la vista previa y la etiqueta de estado."""
        self.preview.setEnabled(enabled)
        self.label.setEnabled(enabled)

    # -- Conversion ---------------------------------------------------------

    @property
    def cache_path(self):
        cache_dir = os.path.expanduser(self.CACHE_DIR)
        os.makedirs(cache_dir, exist_ok=True)
        return os.path.join(cache_dir, self.cache_name)

    def _prepare(self, image):
        """Convierte/reduce la imagen a un PNG que quepa en el Kickstart."""
        target = self.cache_path
        candidate = image
        max_dim = 4096
        if candidate.width() > max_dim or candidate.height() > max_dim:
            candidate = candidate.scaled(
                max_dim,
                max_dim,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        while True:
            if candidate.save(target, "PNG"):
                if os.path.getsize(target) <= self.max_bytes:
                    return target

            if candidate.width() <= 640 and candidate.height() <= 640:
                break
            candidate = candidate.scaled(
                max(1, int(candidate.width() * 0.8)),
                max(1, int(candidate.height() * 0.8)),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        QMessageBox.warning(
            self.owner,
            "Imagen demasiado grande",
            f"No se pudo reducir la imagen a menos de {self.limit_label}. "
            "Usa una imagen mas liviana.",
        )
        return None

    # -- Vista previa -------------------------------------------------------

    def update_display(self, converted=False):
        if not self.path or not os.path.isfile(self.path):
            self.preview.clear()
            self.preview.setText(self.empty_preview_text)
            self.label.setText(self.default_label_text)
            self.label.setToolTip("")
            return

        image = QImage(self.path)
        if image.isNull():
            self.preview.clear()
            self.preview.setText("Imagen no valida")
            self.label.setText(self.path)
            return

        pixmap = QPixmap.fromImage(image)
        self.preview.setPixmap(
            pixmap.scaled(
                self.preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        kib = os.path.getsize(self.path) / 1024
        note = " (convertida a PNG)" if converted else ""
        source = self.source_path or self.path
        self.label.setText(
            f"{os.path.basename(source)} — {image.width()}x{image.height()} px — "
            f"{kib:.0f} KiB{note}\n{self.path}"
        )
        self.label.setToolTip(self.path)
