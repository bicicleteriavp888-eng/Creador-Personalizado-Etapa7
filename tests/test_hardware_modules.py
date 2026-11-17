"""Pruebas de los módulos de hardware del motor Fedora Desktop (Etapa 5)."""

import pytest

from core.desktops import (
    DESKTOP_ENVIRONMENTS,
    DesktopPackageError,
    KIOSK_ONLY_ENTRIES,
    UnknownHardwareModuleError,
    get_hardware_module,
    hardware_module_keys,
    list_hardware_modules,
    resolve_desktop_packages,
    resolve_hardware_packages,
)


def _entries(sections):
    return [entry for _title, entries in sections for entry in entries]


def test_catalogo_de_modulos_tiene_los_modulos_esperados():
    assert hardware_module_keys() == (
        "graphics",
        "wifi",
        "touchpad",
        "wifi_live_assistant",
    )
    names = {key for key, _name, _description in list_hardware_modules()}
    assert names == set(hardware_module_keys())
    assert get_hardware_module("graphics")["enabled"] is True


def test_modulo_desconocido_se_rechaza():
    with pytest.raises(UnknownHardwareModuleError):
        get_hardware_module("sonido")


def test_resolve_hardware_paquetes_ignora_modulos_no_solicitados():
    assert resolve_hardware_packages("gnome") == []


def test_resolve_hardware_grupos_wifi_y_graphics():
    entries = resolve_hardware_packages("kde", modules=["wifi", "graphics"])
    assert "NetworkManager-wifi" in entries
    assert "mesa-dri-drivers" in entries
    assert "libinput" not in entries


def test_resolve_hardware_wifi_live_assistant_activa_red():
    entries = resolve_hardware_packages("gnome", wifi_live_assistant=True)
    assert "NetworkManager-wifi" in entries
    assert "wpa_supplicant" in entries
    assert "linux-firmware" in entries


def test_resolve_hardware_deduplica_y_rechaza_paquetes_invalidos():
    entries = resolve_hardware_packages("xfce", modules=["wifi", "wifi"])
    assert entries.count("NetworkManager-wifi") == 1
    with pytest.raises(UnknownHardwareModuleError):
        resolve_hardware_packages("gnome", modules=["not-a-valid-module"])


def test_resolve_hardware_no_incluye_componentes_de_kiosco():
    entries = resolve_hardware_packages("kde", modules=["graphics", "wifi"])
    assert not (set(entries) & KIOSK_ONLY_ENTRIES)


def test_resolve_desktop_packages_integra_modulos_de_hardware():
    sections = resolve_desktop_packages("gnome", hardware_modules=["wifi"])
    entries = _entries(sections)
    assert "NetworkManager-wifi" in entries
    assert "mesa-dri-drivers" in entries

    sections = resolve_desktop_packages("gnome", wifi_live_assistant=True)
    entries = _entries(sections)
    assert "NetworkManager-wifi" in entries
    assert "wpa_supplicant" in entries


def test_resolve_desktop_packages_sin_modulos_no_agrega_hardware():
    base = resolve_desktop_packages("gnome")
    flat = _entries(base)
    assert "mesa-dri-drivers" in flat
    assert "NetworkManager-wifi" in flat
    assert not any(
        entry.startswith("Hardware y compatibilidad") for entry in flat
    )


def test_resolve_desktop_packages_rechaza_modulos_desconocidos():
    with pytest.raises(UnknownHardwareModuleError):
        resolve_desktop_packages("gnome", hardware_modules=["cage"])


def test_kickstart_del_engine_aplica_modulos_de_hardware(tmp_path):
    from core.desktops import DesktopKickstartGenerator

    generator = DesktopKickstartGenerator(
        {
            "desktop_environment": "gnome",
            "desktop_user": "tester",
            "password_hash": "$6$testsalt$" + "x" * 86,
            "hardware_modules": ["wifi"],
            "wifi_live_assistant": True,
        }
    )
    kickstart = generator.render()
    assert "NetworkManager-wifi" in kickstart
    assert "mesa-dri-drivers" in kickstart
    assert "cage" not in kickstart
