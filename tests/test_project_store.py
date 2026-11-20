import json
from pathlib import Path

import pytest

from core.projects.manager import ProjectStore
from core.projects.catalog import get_project_template


def test_project_store_keeps_each_project_configuration_independent(tmp_path):
    store = ProjectStore(tmp_path / "projects")
    first = store.create("Kiosco Atención", "kiosk", {
        "project_type": "kiosk", "engine": "kiosk", "app_url": "https://kiosco.example",
        "selected_packages": ["chromium"], "password": "never-save-this",
        "ssh_password_auth": False,
    })
    second = store.create("Oficina Central", "office", {
        "project_type": "office", "engine": "desktop", "desktop_environment": "gnome",
        "selected_packages": ["libreoffice-writer"],
    })

    store.save(first["path"], {**first["config"], "app_url": "https://turnos.example"})

    loaded_first = store.load(first["path"])
    loaded_second = store.load(second["path"])
    assert loaded_first["config"]["app_url"] == "https://turnos.example"
    assert loaded_second["config"]["desktop_environment"] == "gnome"
    assert "app_url" not in loaded_second["config"]
    saved_config = json.loads((Path(first["path"]) / "project.json").read_text())['config']
    assert "password" not in saved_config
    assert saved_config["ssh_password_auth"] is False
    assert loaded_first["id"] != loaded_second["id"]


def test_project_store_copies_project_assets_and_resolves_them(tmp_path):
    store = ProjectStore(tmp_path / "projects")
    image = tmp_path / "brand.png"
    image.write_bytes(b"test-image")
    project = store.create("Kiosco Marca", "kiosk", {
        "project_type": "kiosk", "plymouth_image": str(image),
    })
    saved = Path(project["path"]) / "assets" / "plymouth_image" / "brand.png"
    assert saved.is_file()
    assert Path(project["config"]["plymouth_image"]) == saved
    assert saved.read_bytes() == b"test-image"


def test_project_store_rejects_empty_name(tmp_path):
    store = ProjectStore(tmp_path / "projects")
    with pytest.raises(ValueError):
        store.create("  ", "custom", {})


def test_profile_catalog_returns_isolated_precarga():
    template = get_project_template("kiosk")
    template["defaults"]["app_url"] = "changed"
    assert get_project_template("kiosk")["defaults"]["app_url"] == "http://localhost"


def test_all_precargas_keep_engine_separate():
    from core.projects.catalog import list_project_types
    for key, _name, _tagline in list_project_types():
        profile = get_project_template(key)
        expected = "kiosk" if key == "kiosk" else "desktop"
        assert profile["engine"] == expected
        assert profile["defaults"]


def test_named_profile_precargas_match_existing_profile_files():
    from core.projects.catalog import list_named_profiles, get_named_profile_template
    profiles = {item["id"]: item for item in list_named_profiles()}
    assert set(profiles) == {
        "estacion-trabajo", "kiosco-multiventana", "kiosco-navegador",
        "oficina", "terminal-atencion",
    }
    assert profiles["terminal-atencion"]["config"]["app_url"] == "https://atencion.tallerarg.org"
    assert profiles["kiosco-multiventana"]["config"]["multi_app"] is True
    assert profiles["kiosco-navegador"]["config"]["multi_app"] is False
    assert get_named_profile_template("estacion-trabajo")["engine"] == "desktop"
    assert get_named_profile_template("terminal-atencion")["engine"] == "kiosk"


def test_project_store_keeps_build_output_relative_to_project(tmp_path):
    store = ProjectStore(tmp_path / "projects")
    project = store.create("Proyecto Relocalizable", "kiosk", {
        "project_type": "kiosk", "output_dir": str(tmp_path / "projects" / "temp" / "builds"),
    })
    project_dir = Path(project["path"])
    store.save(project_dir, {**project["config"], "output_dir": str(project_dir / "builds")})
    manifest = json.loads((project_dir / "project.json").read_text())
    assert manifest["config"]["output_dir"] == "builds"
    assert Path(store.load(project_dir)["config"]["output_dir"]) == project_dir / "builds"


def test_installer_branding_assets_and_text_are_isolated_per_project(tmp_path):
    store = ProjectStore(tmp_path / "projects")
    banner_kiosk = tmp_path / "kiosk-banner.png"
    banner_desktop = tmp_path / "desktop-banner.png"
    banner_kiosk.write_bytes(b"kiosk-image")
    banner_desktop.write_bytes(b"desktop-image")

    kiosk = store.create("Kiosco Marca", "kiosk", {
        "project_type": "kiosk", "engine": "kiosk",
        "installer_banner": str(banner_kiosk),
        "installer_text": "Bienvenido al Kiosco",
    })
    desktop = store.create("Desktop Marca", "office", {
        "project_type": "office", "engine": "desktop",
        "installer_banner": str(banner_desktop),
        "installer_text": "Bienvenido al Escritorio",
    })

    kiosk_loaded = store.load(kiosk["path"])
    desktop_loaded = store.load(desktop["path"])
    assert Path(kiosk_loaded["config"]["installer_banner"]).read_bytes() == b"kiosk-image"
    assert Path(desktop_loaded["config"]["installer_banner"]).read_bytes() == b"desktop-image"
    assert kiosk_loaded["config"]["installer_text"] == "Bienvenido al Kiosco"
    assert desktop_loaded["config"]["installer_text"] == "Bienvenido al Escritorio"
