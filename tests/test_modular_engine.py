"""Pruebas unitarias para los nuevos módulos de Etapa 4 (Motor Modular)."""

import os
import tempfile
import pytest

from core.kickstart.validator import validate_kickstart_content
from core.kickstart.parser import parse_packages_from_kickstart
from core.iso.iso_inspector import calculate_sha256, inspect_iso_metadata
from core.validation.iso_validator import validate_iso_package
from core.validation.report_generator import generate_txt_report, generate_html_report


def test_kickstart_validator_valid():
    ks = """text
bootloader --location=mbr
clearpart --all
part / --size 10240
%packages
@core
kernel
%end
%post --erroronfail
echo test
%end
"""
    issues = validate_kickstart_content(ks)
    assert not any(level == "error" for level, _ in issues)


def test_kickstart_validator_missing_directives():
    ks = "echo hello"
    issues = validate_kickstart_content(ks)
    assert any(level == "error" for level, _ in issues)


def test_kickstart_parser_packages():
    ks = """%packages
kernel
dracut
firefox
%end"""
    pkgs = parse_packages_from_kickstart(ks)
    assert "kernel" in pkgs
    assert "firefox" in pkgs


def test_iso_inspector_nonexistent():
    meta = inspect_iso_metadata("/nonexistent/path/image.iso")
    assert "error" in meta


def test_iso_validator_nonexistent():
    res = validate_iso_package("/nonexistent/path/image.iso")
    assert res["exists"] is False
    assert len(res["errors"]) > 0


def test_report_generators():
    data = {
        "path": "/tmp/test.iso",
        "size_mb": 500.0,
        "sha256": "abcdef123456",
        "bios_compatible": True,
        "uefi_compatible": True,
        "kickstart_valid": True,
        "errors": [],
        "warnings": ["Advertencia menor"],
    }
    txt = generate_txt_report(data)
    assert "INFORME DE LABORATORIO ISO" in txt
    assert "abcdef123456" in txt

    html = generate_html_report(data)
    assert "<html" in html
    assert "abcdef123456" in html
