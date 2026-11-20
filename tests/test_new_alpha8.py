import json
from pathlib import Path

import pytest

from core.config import BuildConfig, load_project_config
from core.hardware.scanner import _pci_devices, _usb_devices, _recommend, export_hardware_profile, load_hardware_profile
from core.kickstart.validator import validate_kickstart_content, validate_kickstart_file
from core.iso.qemu_smoke import run_qemu_smoke
from core.cache import cache_info


def test_build_config_preserves_legacy_keys_and_types():
    model = BuildConfig.from_mapping({"engine": "desktop", "desktop_environment": "xfce",
                                      "legacy_key": "kept"})
    result = model.to_dict()
    assert result["engine"] == "desktop"
    assert result["legacy_key"] == "kept"
    assert model.desktop_environment == "xfce"


def test_build_config_rejects_kickstart_autoinstall_on_live_iso():
    model = BuildConfig.from_mapping({"engine": "desktop", "auto_install_enabled": True})
    with pytest.raises(ValueError, match="no admite Kickstart automatizado"):
        model.validate()


def test_load_project_config_reads_wrapped_project_json(tmp_path):
    path = tmp_path / "project.json"
    path.write_text(json.dumps({"config": {"engine": "desktop", "iso_name": "Test"}}))
    assert load_project_config(path)["engine"] == "desktop"


def test_build_config_does_not_override_legacy_project_type_engine():
    model = BuildConfig.from_mapping({"project_type": "desktop"})
    model.validate()
    assert model.engine == ""
    assert model.project_type == "desktop"


def test_parse_lspci_and_lsusb_devices():
    pci = _pci_devices("03:00.0 Network controller [0280]: Broadcom Inc. [14e4:43a0]\n\tKernel driver in use: wl")
    usb = _usb_devices("Bus 001 Device 002: ID 0bda:8153 Realtek USB Ethernet")
    assert pci[0]["vendor_device"] == "14e4:43a0"
    assert pci[0]["driver"] == "wl"
    assert usb[0]["vendor_device"] == "0bda:8153"


def test_hardware_recommendations_mark_third_party_driver_manual():
    devices = [{"description": "Network controller", "vendor_device": "14e4:43a0"}]
    recs = {item["package"]: item for item in _recommend(devices)}
    assert recs["linux-firmware"]["requires_external_repo"] is False
    assert recs["akmod-wl"]["requires_external_repo"] is True


def test_hardware_profile_roundtrip_and_reject_invalid_packages(tmp_path):
    path = tmp_path / "legacy.json"
    export_hardware_profile(path, {"pci_devices": []}, "Portátil Legacy", "1366x768", ["linux-firmware"])
    profile = load_hardware_profile(path)
    assert profile["name"] == "Portátil Legacy"
    assert profile["resolution"] == "1366x768"
    profile["selected_packages"] = ["bad package"]
    path.write_text(json.dumps(profile))
    with pytest.raises(ValueError, match="paquetes inválidos"):
        load_hardware_profile(path)


def test_kickstart_static_validator_reports_required_directives():
    issues = validate_kickstart_content("text\n%packages\n%end\n")
    assert any(kind == "error" and "bootloader" in message for kind, message in issues)


def test_kickstart_static_validator_detects_unclosed_post_section():
    issues = validate_kickstart_content(
        "text\nbootloader --location=mbr\npart / --size 1024\n"
        "%packages\n@core\n%end\n%post --erroronfail\necho test\n"
    )
    assert any(kind == "error" and "no tiene %end" in message for kind, message in issues)


def test_kickstart_file_reports_internal_fallback_when_binary_missing(tmp_path, monkeypatch):
    path = tmp_path / "valid.ks"
    path.write_text("text\nbootloader --location=mbr\npart / --size 1024\n%packages\n@core\n%end\n")
    monkeypatch.setattr("core.kickstart.validator.shutil.which", lambda _name: None)
    report = validate_kickstart_file(path, "44")
    assert report["validator"] == "internal"
    assert report["official"] is False
    assert report["ok"] is True


def test_qemu_smoke_reports_missing_iso(tmp_path):
    result = run_qemu_smoke(str(tmp_path / "missing.iso"))
    assert result["status"] == "INVALID_ISO"


def test_kickstart_file_invokes_official_validator_when_available(tmp_path, monkeypatch):
    import subprocess
    path = tmp_path / "valid.ks"
    path.write_text("text\nbootloader --location=mbr\npart / --size 1024\n%packages\n@core\n%end\n")
    calls = []
    monkeypatch.setattr("core.kickstart.validator.shutil.which", lambda _name: "/usr/bin/ksvalidator")
    def fake_run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")
    monkeypatch.setattr("core.kickstart.validator.subprocess.run", fake_run)
    report = validate_kickstart_file(path, "44")
    assert report["official"] is True
    assert report["ok"] is True
    assert calls[0][1:3] == ["-v", "F44"]


def test_cache_info_reports_persistent_cache_size(tmp_path):
    cached = tmp_path / "cached.rpm"
    cached.write_bytes(b"12345")
    info = cache_info(str(tmp_path))
    assert info["exists"] is True
    assert info["size_bytes"] == 5
