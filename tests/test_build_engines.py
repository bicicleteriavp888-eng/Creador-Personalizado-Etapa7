"""Pruebas de integración del motor Desktop en el constructor (Etapa 3)."""

import os

import pytest

from core.builder import KioskISOBuilder
from core.builders import (
    DEFAULT_BUILD_ENGINE,
    BuildEngineError,
    DesktopISOBuilder,
    resolve_build_engine,
    resolve_builder_class,
)
from core.desktops import DesktopKickstartError, UnknownDesktopEnvironmentError
from core.desktops.packages import DesktopPackageError
from core.kickstart.parser import parse_packages_from_kickstart

FAKE_HASH = "$6$testsalt$" + ("x" * 86)


def _config(tmp_path, **overrides):
    config = {
        "engine": "desktop",
        "desktop_environment": "gnome",
        "desktop_user": "tester",
        "iso_name": "Fedora Desktop Test",
        "version": "1.0",
        "developer": "Tester",
        "release": "44",
        "boot_mode": "dual",
        "password": "clave-inicial",
        "extra_packages": "",
        "extra_groups": "",
        "enable_installer": True,
        "enable_firewall": True,
        "enable_ssh": False,
        "output_dir": str(tmp_path / "ISOs"),
    }
    config.update(overrides)
    return config


def test_engine_ausente_sigue_siendo_kiosk():
    assert DEFAULT_BUILD_ENGINE == "kiosk"
    assert resolve_build_engine({}) == "kiosk"
    assert resolve_build_engine({"project_type": "kiosk"}) == "kiosk"


def test_engine_explicito_y_por_perfil():
    assert resolve_build_engine({"engine": "desktop"}) == "desktop"
    assert resolve_build_engine({"engine": "KIOSK"}) == "kiosk"
    assert resolve_build_engine({"project_type": "office"}) == "desktop"
    assert resolve_build_engine({"project_type": "security_lab"}) == "desktop"


def test_engine_explicito_tiene_prioridad_sobre_el_perfil():
    assert (
        resolve_build_engine({"engine": "kiosk", "project_type": "office"})
        == "kiosk"
    )


def test_engine_desconocido_o_perfil_invalido_se_rechaza():
    with pytest.raises(BuildEngineError):
        resolve_build_engine({"engine": "gnome"})
    with pytest.raises(BuildEngineError):
        resolve_build_engine({"project_type": "inexistente"})


def test_resolver_devuelve_las_clases_de_cada_motor():
    assert resolve_builder_class({}) is KioskISOBuilder
    assert resolve_builder_class({"engine": "kiosk"}) is KioskISOBuilder
    assert resolve_builder_class({"engine": "desktop"}) is DesktopISOBuilder
    assert resolve_builder_class({"project_type": "web"}) is DesktopISOBuilder


def test_desktop_builder_usa_archivos_y_generador_propios(tmp_path):
    builder = DesktopISOBuilder(_config(tmp_path))
    assert builder.ks_path.endswith("desktop.ks")
    assert builder.log_path.endswith("desktop-build.log")
    assert builder.ks_path != os.path.join(builder.work_dir, "kiosk.ks")
    assert builder.desktop_generator.environment["name"] == "GNOME"
    assert builder.engine == "desktop"


def test_desktop_builder_genera_kickstart_sin_componentes_de_kiosco(tmp_path):
    builder = DesktopISOBuilder(
        _config(
            tmp_path,
            desktop_environment="kde",
            extra_groups="@office",
            extra_packages="htop",
        )
    )
    builder.work_dir = str(tmp_path)
    builder.ks_path = str(tmp_path / "desktop.ks")

    builder._generate_kickstart(FAKE_HASH)
    kickstart = (tmp_path / "desktop.ks").read_text(encoding="utf-8")
    packages = parse_packages_from_kickstart(kickstart)

    assert "sddm" in packages
    assert "sddm.service" in kickstart
    assert "@office" in packages
    assert "htop" in packages
    assert "tester" in kickstart
    for forbidden in ("cage", "sway", "seatd", "kioskuser", "kiosk.service"):
        assert forbidden not in packages
        assert forbidden not in kickstart


def test_desktop_builder_valida_antes_de_compilar(tmp_path):
    builder = DesktopISOBuilder(_config(tmp_path))
    builder.validate_configuration()

    with pytest.raises(DesktopPackageError):
        DesktopISOBuilder(
            _config(tmp_path, extra_packages="telnet")
        ).validate_configuration()

    with pytest.raises(DesktopKickstartError):
        DesktopISOBuilder(_config(tmp_path, desktop_user="Root")).validate_configuration()

    missing_password = _config(tmp_path)
    missing_password.pop("password")
    with pytest.raises(DesktopKickstartError):
        DesktopISOBuilder(missing_password).validate_configuration()

    with pytest.raises(UnknownDesktopEnvironmentError):
        DesktopISOBuilder(_config(tmp_path, desktop_environment="cinnamon"))


def test_mensajes_de_cierre_distinguen_kiosk_y_desktop(tmp_path):
    kiosk = KioskISOBuilder(
        {"iso_name": "TestKiosk", "app_mode": "chromium", "password": "x"}
    )
    assert "kioskuser" in " ".join(kiosk._build_success_messages())

    desktop = DesktopISOBuilder(_config(tmp_path, enable_ssh=True))
    messages = " ".join(desktop._build_success_messages())
    assert "tester" in messages
    assert "GNOME" in messages
    assert "kioskuser" not in messages


def test_builder_worker_usa_el_motor_resuelto(monkeypatch):
    import main

    class FakeSignal:
        def connect(self, slot):
            self.slot = slot

    selected = []

    class FakeBuilder:
        log_signal = FakeSignal()
        progress_signal = FakeSignal()

        def __init__(self, config):
            selected.append(config)
            self.cancel_event = None
            self.last_iso_path = ""

        def build(self):
            return True

    monkeypatch.setattr(
        main, "resolve_builder_class", lambda config: FakeBuilder
    )
    worker = main.BuilderWorker({"engine": "desktop"})
    finished = []
    worker.finished_signal.connect(finished.append)
    worker.run()

    assert selected == [{"engine": "desktop"}]
    assert finished == [True]
