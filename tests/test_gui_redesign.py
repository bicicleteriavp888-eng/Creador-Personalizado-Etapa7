"""Pruebas de la renovación de interfaz: adaptación, estado y cierre seguro."""

import os
import sqlite3
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication, QScrollArea, QSizePolicy

from gui.components import prepare_combo
from gui.status import recent_builds
from gui.theme import THEMES
from main import KioskBuilderGUI, STEP_KEYS


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app, tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    widget = KioskBuilderGUI()
    widget.resize(1080, 720)
    widget.show()
    app.processEvents()
    yield widget
    widget.close()
    app.processEvents()


class _SlowWorker(QThread):
    """Hilo de prueba que simula una consulta DNF todavía en curso."""

    def __init__(self, delay=0.25):
        super().__init__()
        self.delay = delay
        self.completed = False

    def run(self):
        time.sleep(self.delay)
        self.completed = True


def test_manager_and_step1_have_independent_project_type_combos(window, app):
    step1 = window._pages["step1"]["widget"]
    assert step1.isAncestorOf(window.combo_project_type)
    assert not step1.isAncestorOf(window.combo_manager_project_type)
    window._navigate("step1", validate=False)
    app.processEvents()
    assert window.combo_project_type.isVisible()

    window.combo_manager_project_type.setCurrentIndex(
        window.combo_manager_project_type.findData("office")
    )
    app.processEvents()
    assert window._project_type == "office"
    assert window.combo_project_type.currentData() == "office"

    window.combo_project_type.setCurrentIndex(
        window.combo_project_type.findData("gaming")
    )
    app.processEvents()
    assert window.combo_manager_project_type.currentData() == "gaming"


def test_manager_status_does_not_overwrite_wizard_status(window):
    window.lbl_wizard_status.setText("Paso 1 de 6 · estado global")
    window._set_manager_status("Mensaje propio del gestor")
    assert window.lbl_wizard_status.text() == "Paso 1 de 6 · estado global"
    assert window.lbl_manager_status.text() == "Mensaje propio del gestor"


def test_manager_table_exposes_architecture_and_type(window):
    labels = [
        window.table_fedora_available.horizontalHeaderItem(index).text()
        for index in range(window.table_fedora_available.columnCount())
    ]
    assert labels == [
        "Paquete",
        "Descripción",
        "Versión",
        "Arquitectura",
        "Repositorio",
        "Tipo",
    ]
    assert window.table_fedora_pending.columnCount() == 2


def test_prepare_combo_does_not_force_page_width(window, app):
    combo = prepare_combo(window.combo_manager_project_type, 12)
    assert combo.minimumWidth() >= 150
    assert (
        combo.sizePolicy().horizontalPolicy()
        == QSizePolicy.Policy.Ignored
    )


def test_close_waits_for_running_dnf_worker(window, app):
    worker = _SlowWorker()
    window._custom_pkg_worker = worker
    worker.start()

    closed = window.close()
    app.processEvents()

    assert closed is True
    assert worker.completed is True
    assert worker.isRunning() is False
    assert window._custom_pkg_worker is None


def test_dashboard_service_query_is_async(window, app, monkeypatch):
    def slow_states(names):
        time.sleep(0.35)
        return {"firewalld": "active", "sshd": "inactive"}

    monkeypatch.setattr("gui.status.service_states", slow_states)
    if window._host_status_worker is not None:
        window._host_status_worker.wait(5000)
    window._service_states_cache = {}
    window._last_host_query = 0.0

    started = time.monotonic()
    window.refresh_dashboard()
    elapsed = time.monotonic() - started

    assert elapsed < 0.30
    assert window.card_services.value.text() == "Consultando…"
    worker = window._host_status_worker
    assert worker.wait(5000)
    for _ in range(10):
        app.processEvents()
    assert "firewalld: active" in window.card_services.value.text()


def test_common_pages_have_no_horizontal_scroll_at_minimum_size(window, app):
    window.resize(1080, 720)
    window._dnf_available = False  # evita consultar repositorios durante el test
    app.processEvents()
    for key in ("dashboard",) + STEP_KEYS + ("custom_distro", "usb"):
        assert window._navigate(key, validate=False)
        for _ in range(3):
            app.processEvents()
        page = window._pages[key]["widget"]
        for scroll in page.findChildren(QScrollArea):
            assert scroll.horizontalScrollBar().maximum() == 0, key


def test_theme_has_aa_contrast_and_table_rules():
    def luminance(color):
        values = []
        for index in (1, 3, 5):
            channel = int(color[index : index + 2], 16) / 255
            values.append(
                channel / 12.92
                if channel <= 0.04045
                else ((channel + 0.055) / 1.055) ** 2.4
            )
        return 0.2126 * values[0] + 0.7152 * values[1] + 0.0722 * values[2]

    def ratio(foreground, background):
        light, dark = sorted(
            (luminance(foreground), luminance(background)), reverse=True
        )
        return (light + 0.05) / (dark + 0.05)

    for name, palette in THEMES.items():
        assert ratio(palette["TEXT"], palette["BG"]) >= 7.0, name
        assert ratio(palette["TEXT"], palette["SURFACE_ALT"]) >= 7.0, name
        assert ratio(palette["MUTED"], palette["SURFACE"]) >= 4.5, name
        assert ratio(palette["MUTED"], palette["BG"]) >= 4.5, name
        assert ratio(palette["ACCENT"], palette["SURFACE"]) >= 4.5, name
        assert ratio(palette["DANGER"], palette["SURFACE"]) >= 4.5, name

    from gui.theme import build_stylesheet

    for theme in ("light", "dark"):
        css = build_stylesheet(theme)
        for selector in (
            "QTableWidget",
            "QHeaderView::section",
            "QSplitter::handle",
            "QDialog",
            "QTableWidget::item:selected",
        ):
            assert selector in css


def test_recent_builds_reads_only_existing_history(tmp_path):
    missing = tmp_path / "no-existe.sqlite3"
    assert recent_builds(database=missing) == []
    assert not missing.exists()

    database = tmp_path / "history.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE builds (build_id TEXT PRIMARY KEY, started_at REAL NOT NULL, "
        "finished_at REAL, status TEXT NOT NULL, iso_path TEXT, iso_sha256 TEXT, "
        "log_path TEXT, config_json TEXT NOT NULL, error TEXT)"
    )
    connection.execute(
        "INSERT INTO builds(build_id, started_at, status, iso_path, config_json) "
        "VALUES(?,?,?,?,?)",
        ("b1", 1700000000.0, "GENERATED", str(tmp_path / "Uno.iso"), "{}"),
    )
    connection.commit()
    connection.close()

    rows = recent_builds(limit=3, database=database)
    assert len(rows) == 1
    assert rows[0]["status"] == "GENERATED"
    assert rows[0]["iso_path"].endswith("Uno.iso")
