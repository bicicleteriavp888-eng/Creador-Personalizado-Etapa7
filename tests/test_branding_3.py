from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]

def test_pyproject_uses_new_product_identity_and_keeps_legacy_cli():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert data["project"]["name"] == "creador-personalizado"
    assert data["project"]["version"] == "3.0.0a9"
    scripts = data["project"]["scripts"]
    assert scripts["creador-personalizado"] == "main:main"
    assert scripts["creador-kiosk"] == "main:main"

def test_desktop_entry_and_launcher_use_new_brand():
    desktop = (ROOT / "packaging/creador-personalizado.desktop").read_text()
    launcher = (ROOT / "scripts/creador-personalizado").read_text()
    assert "Name=Creador Personalizado" in desktop
    assert "Exec=creador-personalizado" in desktop
    assert "/opt/creador-personalizado" in launcher

def test_architecture_document_records_real_builder_inheritance_limit():
    doc = (ROOT / "documentation/ARQUITECTURA_3.0.md").read_text()
    assert "DesktopISOBuilder" in doc
    assert "heredando de `KioskISOBuilder`" in doc
    assert "Pendiente" in doc
