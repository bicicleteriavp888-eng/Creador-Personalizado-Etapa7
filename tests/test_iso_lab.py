from core.iso.iso_inspector import inspect_iso_metadata
from core.kickstart.validator import validate_kickstart_content
from core.validation.iso_validator import validate_iso_package


def test_iso_inspector_reports_missing_file(tmp_path):
    result = inspect_iso_metadata(str(tmp_path / "missing.iso"))
    assert "error" in result


def test_iso_inspector_hashes_file_without_claiming_boot(tmp_path):
    image = tmp_path / "fixture.iso"
    image.write_bytes(b"not-a-real-iso" * 100)
    result = inspect_iso_metadata(str(image))
    assert len(result["sha256"]) == 64
    assert result["has_efi"] is False
    assert result["has_isolinux"] is False


def test_kickstart_validator_detects_missing_required_sections():
    issues = validate_kickstart_content("text\n")
    assert any(kind == "error" for kind, _ in issues)


def test_iso_validation_missing_path_is_error(tmp_path):
    result = validate_iso_package(str(tmp_path / "none.iso"))
    assert result["exists"] is False
    assert result["errors"]


def test_report_marks_qemu_unavailable_and_escapes_html():
    from core.validation.report_generator import generate_txt_report, generate_html_report
    data = {"path": "<script>alert(1)</script>", "qemu": {"bios": {"status": "NOT_AVAILABLE", "boot_markers": []}}}
    assert "BIOS: NOT_AVAILABLE" in generate_txt_report(data)
    assert "&lt;script&gt;" in generate_html_report(data)
