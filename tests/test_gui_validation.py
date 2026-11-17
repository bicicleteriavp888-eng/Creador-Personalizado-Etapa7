"""Pruebas de la validacion por etapas del asistente 2.0."""

import shutil
from collections import namedtuple

from gui import validation


Usage = namedtuple("Usage", "total used free")


def _config(tmp_path, **overrides):
    config = {
        "iso_name": "TallerArgOS-kiosk",
        "version": "1.0.0",
        "developer": "Sergio",
        "product_name": "TallerArgOS Fedora Kiosk",
        "password": "clave-segura-123",
        "boot_mode": "dual",
        "app_mode": "chromium",
        "app_url": "http://localhost",
        "app_path": "",
        "multi_app": False,
        "app2_mode": "chromium",
        "app2_url": "",
        "app2_command": "",
        "app2_path": "",
        "extra_packages": "",
        "plymouth_image": "",
        "installer_banner": "",
        "enable_ssh": False,
        "ssh_password_auth": False,
        "output_dir": str(tmp_path / "ISOs"),
    }
    config.update(overrides)
    return config


def _fake_environment(monkeypatch, free=20 * 1024 ** 3):
    monkeypatch.setattr(
        "gui.status.check_dependencies",
        lambda: {
            "ok": True,
            "missing": [],
            "available": 7,
            "total": 7,
            "tools": [],
            "assets": [],
        },
    )
    monkeypatch.setattr(
        shutil, "disk_usage", lambda path: Usage(100 * 1024 ** 3, 0, free)
    )


def test_valid_configuration_has_no_issues(tmp_path, monkeypatch):
    _fake_environment(monkeypatch)
    assert validation.validate_all(_config(tmp_path)) == []


def test_identity_rejects_control_characters_and_invalid_names(tmp_path):
    base = _config(tmp_path, project_type="office")
    issues = validation.validate_identity(
        dict(
            base,
            password="clave\ninyectada",
            iso_name="con espacio",
            version="-1",
            developer="x" * 81,
        )
    )
    messages = " ".join(issue.message for issue in issues)
    titles = " ".join(issue.title for issue in issues)
    assert "128 caracteres" in messages
    assert "Nombre de ISO" in titles
    assert "Version" in titles
    assert "Creador" in titles
    assert {issue.step for issue in issues} == {1}


def test_desktop_identity_accepts_short_initial_password(tmp_path):
    assert validation.validate_identity(
        _config(tmp_path, project_type="office", password="x")
    ) == []


def test_kiosk_identity_does_not_require_password(tmp_path):
    assert validation.validate_identity(_config(tmp_path, password="")) == []


def test_desktop_identity_requires_valid_password(tmp_path):
    for password in ("", "x" * 129):
        issues = validation.validate_identity(
            _config(tmp_path, project_type="office", password=password)
        )
        assert any("Contrasena inicial" in issue.title for issue in issues)


def test_desktop_identity_accepts_short_initial_password(tmp_path):
    assert validation.validate_identity(
        _config(tmp_path, project_type="office", password="x")
    ) == []


def test_kiosk_identity_does_not_require_password(tmp_path):
    assert validation.validate_identity(_config(tmp_path, password="")) == []


def test_desktop_identity_requires_valid_password(tmp_path):
    for password in ("", "x" * 129):
        issues = validation.validate_identity(
            _config(tmp_path, project_type="office", password=password)
        )
        assert any("Contrasena inicial" in issue.title for issue in issues)


def test_identity_rejects_unsafe_product_name(tmp_path):
    issues = validation.validate_identity(
        _config(tmp_path, product_name='Nombre "raro"')
    )
    assert any("producto" in issue.title for issue in issues)


def test_appearance_checks_images_only_when_present(tmp_path):
    base = _config(tmp_path)
    assert validation.validate_appearance(base) == []

    missing = tmp_path / "no-existe.png"
    issues = validation.validate_appearance(dict(base, plymouth_image=str(missing)))
    assert any(issue.step == 2 and "Falta" in issue.title for issue in issues)

    big = tmp_path / "grande.png"
    big.write_bytes(b"0")
    with big.open("r+b") as handle:
        handle.truncate(4 * 1024 ** 2 + 1)
    issues = validation.validate_appearance(dict(base, plymouth_image=str(big)))
    assert any("demasiado grande" in issue.title for issue in issues)



def test_software_validates_local_apps_packages_and_second_window(tmp_path):
    base = _config(tmp_path)
    issues = validation.validate_software(
        dict(base, app_mode="custom", app_path=str(tmp_path / "no-existe"))
    )
    assert any("Falta la aplicacion" in issue.title for issue in issues)

    issues = validation.validate_software(
        dict(base, extra_packages="htop;rm -rf /")
    )
    assert any("Paquetes no validos" in issue.title for issue in issues)

    issues = validation.validate_software(
        dict(base, extra_packages="telnet")
    )
    assert any("Paquetes bloqueados" in issue.title for issue in issues)

    issues = validation.validate_software(
        dict(base, extra_groups="@office grupo-con-espacios")
    )
    assert any("Grupos no validos" in issue.title for issue in issues)

    issues = validation.validate_software(
        dict(base, multi_app=True, app2_mode="firefox", app2_url="")
    )
    assert any("segunda app" in issue.title for issue in issues)

    issues = validation.validate_software(
        dict(base, multi_app=True, app2_mode="custom", app2_command="a\nb")
    )
    assert any("Comando no valido" in issue.title for issue in issues)

    issues = validation.validate_software(
        dict(base, multi_app=True, app2_mode="local", app2_path="")
    )
    assert any("Falta la segunda aplicacion" in issue.title for issue in issues)


def test_software_desktop_no_exige_aplicacion_de_kiosco(tmp_path):
    base = _config(
        tmp_path,
        engine="desktop",
        desktop_environment="gnome",
        desktop_user="fedora",
        app_mode="custom",
        app_path="",
        multi_app=True,
        app2_mode="local",
        app2_path="",
    )
    assert validation.validate_software(base) == []

    issues = validation.validate_software(
        dict(base, desktop_environment="cinnamon")
    )
    assert any("Escritorio no válido" in issue.title for issue in issues)

    issues = validation.validate_software(dict(base, desktop_user="1usuario"))
    assert any("Usuario de escritorio" in issue.title for issue in issues)

    issues = validation.validate_software(
        dict(base, extra_packages="telnet")
    )
    assert any("bloqueados" in issue.title for issue in issues)


def test_software_desktop_se_resuelve_desde_el_perfil(tmp_path):
    base = _config(tmp_path, project_type="office")
    base.update(
        app_mode="custom",
        app_path="",
        desktop_environment="xfce",
        desktop_user="fedora",
    )
    assert validation.validate_software(base) == []


def test_identity_rechaza_tipo_de_distribucion_desconocido(tmp_path):
    issues = validation.validate_identity(
        dict(_config(tmp_path), project_type="distro-magica")
    )
    assert any(
        issue.step == 1 and "Tipo de distribución" in issue.title for issue in issues
    )


def test_identity_accepts_known_project_types(tmp_path):
    for project_type in ("kiosk", "office", "web", "gaming", "security_lab", "custom"):
        assert validation.validate_identity(
            dict(_config(tmp_path), project_type=project_type)
        ) == []


def test_installer_and_security_validation(tmp_path):
    base = _config(tmp_path)
    issues = validation.validate_installer(
        dict(base, installer_banner=str(tmp_path / "no-existe.png"))
    )
    assert any(issue.step == 4 for issue in issues)

    assert validation.validate_security(base) == []
    issues = validation.validate_security(
        dict(base, enable_ssh=False, ssh_password_auth=True)
    )
    assert any("SSH incoherente" in issue.title for issue in issues)


def test_build_reports_missing_dependencies_and_low_space(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "gui.status.check_dependencies",
        lambda: {
            "ok": False,
            "missing": [{"name": "xorrisofs", "package": "xorriso"}],
            "available": 6,
            "total": 7,
            "tools": [],
            "assets": [],
        },
    )
    monkeypatch.setattr(
        shutil, "disk_usage", lambda path: Usage(100 * 1024 ** 3, 99 * 1024 ** 3, 1024)
    )
    issues = validation.validate_build(_config(tmp_path))
    messages = " ".join(issue.message for issue in issues)
    titles = " ".join(issue.title for issue in issues)
    assert "xorrisofs" in messages
    assert "Espacio insuficiente" in titles
    assert all(issue.step == 6 for issue in issues)


def test_build_rejects_output_path_that_is_a_file(tmp_path, monkeypatch):
    _fake_environment(monkeypatch)
    output = tmp_path / "archivo"
    output.write_text("no es una carpeta")
    issues = validation.validate_build(_config(tmp_path, output_dir=str(output)))
    assert any("no es una carpeta" in issue.message for issue in issues)


def test_build_requires_helpers_for_local_rpm(tmp_path, monkeypatch):
    _fake_environment(monkeypatch)
    monkeypatch.setattr(
        shutil,
        "which",
        lambda name: "/usr/bin/rpm" if name == "rpm" else None,
    )
    rpm = tmp_path / "app.rpm"
    rpm.write_bytes(b"paquete")
    issues = validation.validate_build(
        _config(
            tmp_path,
            app_mode="custom",
            app_path=str(rpm),
            multi_app=False,
        )
    )
    assert any("RPM locales" in issue.title for issue in issues)
    assert any("createrepo_c" in issue.message for issue in issues)


def test_validate_until_uses_passwordless_kiosk_policy(tmp_path, monkeypatch):
    _fake_environment(monkeypatch)
    kiosk = _config(tmp_path, password="")
    assert validation.validate_until(1, kiosk) == []

    desktop = _config(tmp_path, project_type="office", password="")
    issues = validation.validate_until(1, desktop)
    assert issues and all(issue.step == 1 for issue in issues)
    assert validation.validate_until(0, kiosk) == []
