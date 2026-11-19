from core.iso.quick_audit import audit_iso_quick


def test_quick_audit_rejects_missing_iso(tmp_path):
    report = audit_iso_quick(str(tmp_path / "missing.iso"))
    assert report["status"] == "FAIL"
    assert report["errors"]


def test_quick_audit_reports_missing_xorriso(tmp_path, monkeypatch):
    image = tmp_path / "candidate.iso"
    image.write_bytes(b"iso fixture")
    monkeypatch.setattr("core.iso.quick_audit.shutil.which", lambda _name: None)
    report = audit_iso_quick(str(image))
    assert report["status"] == "UNAVAILABLE"
    assert any("xorriso" in item for item in report["warnings"])


def test_quick_audit_reports_grub_and_squashfs_results(tmp_path, monkeypatch):
    image = tmp_path / "candidate.iso"
    image.write_bytes(b"iso fixture")
    monkeypatch.setattr("core.iso.quick_audit.shutil.which", lambda name: "/usr/bin/tool" if name in {
        "xorriso", "grub2-script-check", "unsquashfs"
    } else None)
    monkeypatch.setattr("core.iso.quick_audit._iso_paths", lambda *_: (["/boot/grub2/grub.cfg"], ["/LiveOS/squashfs.img"]))

    def fake_extract(_xorriso, _iso, _member, destination):
        destination.write_bytes(b"fixture")

    def fake_run(command, output_path, timeout=180):
        output_path.write_text("file1\nfile2\n")
        return 0, "", 2

    def fake_command(command, timeout=45):
        from subprocess import CompletedProcess
        return CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("core.iso.quick_audit._extract", fake_extract)
    monkeypatch.setattr("core.iso.quick_audit._run", fake_command)
    monkeypatch.setattr("core.iso.quick_audit._run_listing", fake_run)
    report = audit_iso_quick(str(image))
    assert report["status"] == "PASS"
    assert report["grub_configs"][0]["status"] == "PASS"
    assert report["squashfs_images"][0]["listed_entries"] == 2
