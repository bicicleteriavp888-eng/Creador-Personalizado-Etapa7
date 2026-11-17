"""Paso 6: compilación, validación, progreso y cancelación."""

import os
from gui.layouts import add_page
from PySide6.QtWidgets import (
    QFileDialog, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QProgressBar, QPushButton, QTextEdit, QVBoxLayout, QWidget,
)

HELP = """
<p><b>Compilación y validación</b></p>
<p>Antes de compilar podés validar toda la configuración. La validación
comprueba los datos de las etapas, las imágenes elegidas, los paquetes
adicionales, las dependencias del host y el espacio disponible.</p>
<p>La compilación se ejecuta en segundo plano con <code>livecd-creator</code>.
La interfaz sigue respondiendo, muestra el progreso y el registro, y permite
cancelar. Al finalizar se guarda la ruta, el tamaño y el SHA-256 de la ISO.</p>
<p>Una ISO <b>generada</b> no está automáticamente <b>validada</b> ni
<b>probada</b>. Esas comprobaciones se realizan en las etapas de laboratorio.</p>
"""


class BuildTabMixin:
    """Paso 6: compilación y validación (mixin de KioskBuilderGUI)."""

    def init_tab_build(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        group_output = QGroupBox("Destino de la imagen")
        output_layout = QHBoxLayout(group_output)
        self.txt_output = QLineEdit(os.path.expanduser("~/ISOs"))
        self.txt_output.setPlaceholderText("Carpeta donde se guardará la ISO")
        self.btn_output = QPushButton("Examinar…")
        self.btn_output.clicked.connect(self.select_output_dir)
        output_layout.addWidget(self.txt_output, 1)
        output_layout.addWidget(self.btn_output)

        group_summary = QGroupBox("Resumen del proyecto")
        summary_layout = QVBoxLayout(group_summary)
        self.lbl_build_summary = QLabel("Todavía no hay un resumen disponible.")
        self.lbl_build_summary.setObjectName("cardDetail")
        self.lbl_build_summary.setWordWrap(True)
        summary_layout.addWidget(self.lbl_build_summary)

        group_validation = QGroupBox("Validación previa")
        validation_layout = QVBoxLayout(group_validation)
        self.lbl_validation = QLabel(
            "La configuración todavía no fue validada en esta sesión."
        )
        self.lbl_validation.setObjectName("cardDetail")
        self.lbl_validation.setWordWrap(True)
        validation_layout.addWidget(self.lbl_validation)
        actions = QHBoxLayout()
        self.btn_validate = QPushButton("Validar configuración")
        self.btn_validate.setToolTip(
            "Comprueba las etapas, las dependencias del host y el espacio disponible antes de compilar."
        )
        self.btn_validate.clicked.connect(self.validate_configuration)
        self.btn_build = QPushButton("Generar imagen ISO")
        self.btn_build.setObjectName("primaryAction")
        self.btn_build.clicked.connect(self.start_build_process)
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setToolTip(
            "Aborta livecd-creator y limpia el árbol de trabajo para el próximo intento."
        )
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_build)
        actions.addWidget(self.btn_validate)
        actions.addWidget(self.btn_build, 1)
        actions.addWidget(self.btn_cancel)
        validation_layout.addLayout(actions)

        group_progress = QGroupBox("Estado de compilación")
        progress_layout = QVBoxLayout(group_progress)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        self.txt_logs = QTextEdit()
        self.txt_logs.setObjectName("console")
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setMinimumHeight(180)
        progress_layout.addWidget(QLabel("Registro de livecd-creator:"))
        progress_layout.addWidget(self.txt_logs, 1)

        layout.addWidget(group_output)
        layout.addWidget(group_summary)
        layout.addWidget(group_validation)
        layout.addWidget(group_progress, 1)

        add_page(
            self, "step6", tab, "Compilación y validación",
            "Revisá el proyecto, validá sus requisitos y generá la imagen ISO.",
            HELP, step=6,
        )

    def refresh_build_summary(self):
        """Refresca el resumen de la configuración antes de compilar."""
        config = self.collect_config()
        engine = str(config.get("engine") or "kiosk")
        environment = str(config.get("desktop_environment") or "—")
        lines = [
            f"Motor: {engine} · Escritorio: {environment} · Usuario: {config.get('desktop_user') or '—'}",
            f"ISO: {config.get('iso_name') or '—'} {config.get('version') or '—'} · Producto: {config.get('product_name') or 'Fedora Linux'}",
            f"Arranque: {config.get('boot_mode') or '—'} · Resolución: {config.get('resolution') or 'auto'}",
            f"App: {config.get('app_mode') or '—'} · URL: {config.get('app_url') or '—'}",
            f"Paquetes adicionales: {config.get('extra_packages') or '—'} · Grupos: {config.get('extra_groups') or '—'}",
            f"Firewall: {'ON' if config.get('enable_firewall') else 'OFF'} · SSH: {'ON' if config.get('enable_ssh') else 'OFF'} · Instalador: {'ON' if config.get('enable_installer') else 'OFF'}",
        ]
        self.lbl_build_summary.setText("\n".join(lines))

    def select_output_dir(self):
        path = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta de salida", self.txt_output.text()
        )
        if path:
            self.txt_output.setText(path)

    def build_finished(self, success):
        self.btn_build.setEnabled(True)
        self.btn_build.setText("Generar imagen ISO")
        self.btn_validate.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setText("Cancelar")
        cancelled = (
            self.worker is not None
            and not success
            and self.worker.cancel_event.is_set()
        )
        if success:
            self.txt_logs.append("\n[PROCESO COMPLETADO] La ISO se generó con éxito.")
        elif cancelled:
            self.txt_logs.append("\n[CANCELADO] Compilación abortada por el usuario.")
        else:
            self.txt_logs.append("\n[ERROR] Falló la creación de la ISO. Revisá los registros.")
        if hasattr(self, "_record_build_finished"):
            self._record_build_finished(success, cancelled)

    def cancel_build(self):
        if self.worker is None or not self.worker.isRunning():
            return
        reply = QMessageBox.question(
            self,
            "Cancelar compilación",
            "¿Abortar la compilación en curso?\n\n"
            "Se terminará livecd-creator y se limpiará el árbol de trabajo "
            "para el próximo intento.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setText("CANCELANDO…")
        self.worker.cancel_event.set()
