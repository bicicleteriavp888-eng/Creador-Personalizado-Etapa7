"""Pruebas unitarias para el módulo de seguridad (Etapa 6)."""

import pytest

from core.security.allowlist import is_package_allowed, validate_packages_list
from core.security.rpm_verifier import verify_rpm_signature
from core.security.credentials import password_hash


def test_allowlist_packages():
    assert is_package_allowed("firefox") is True
    assert is_package_allowed("telnet") is False  # en bloqueados
    assert is_package_allowed("malicious;rm -rf") is False


def test_validate_packages_list():
    res = validate_packages_list("firefox, telnet, htop, bad-pkg;inject")
    assert "firefox" in res["allowed"]
    assert "telnet" in res["blocked"]
    assert "bad-pkg;inject" in res["invalid"]


def test_rpm_verifier_nonexistent():
    res = verify_rpm_signature("/nonexistent/package.rpm")
    assert res["signed"] is False
    assert "error" in res


def test_password_hash_accepts_short_initial_password():
    value = password_hash("abc123")
    assert value.startswith("$6$")


def test_password_hash_rejects_empty_and_control_characters():
    for value in ("", "clave\ninyectada"):
        with pytest.raises(RuntimeError):
            password_hash(value)


def test_rpm_verifier_requires_trusted_signature(monkeypatch):
    from types import SimpleNamespace
    import core.security.rpm_verifier as verifier
    monkeypatch.setattr(verifier.shutil, "which", lambda name: "/usr/bin/rpmkeys")
    monkeypatch.setattr(verifier.subprocess, "run", lambda *a, **k: SimpleNamespace(
        returncode=0, stdout="package.rpm: digests signatures OK", stderr=""))
    result = verifier.verify_rpm_signature("package.rpm")
    assert result["verified"] is True
    monkeypatch.setattr(verifier.subprocess, "run", lambda *a, **k: SimpleNamespace(
        returncode=0, stdout="package.rpm: digests OK (GPG) NOKEY", stderr=""))
    result = verifier.verify_rpm_signature("package.rpm")
    assert result["verified"] is False


def test_rpm_verifier_classifies_unsigned_with_valid_digests(monkeypatch):
    from types import SimpleNamespace
    import core.security.rpm_verifier as verifier
    monkeypatch.setattr(verifier.shutil, "which", lambda name: "/usr/bin/rpmkeys")
    monkeypatch.setattr(verifier.subprocess, "run", lambda *a, **k: SimpleNamespace(
        returncode=0, stdout="package.rpm: digests OK", stderr=""))
    result = verifier.verify_rpm_signature("package.rpm")
    assert result["unsigned"] is True
    assert result["digest_ok"] is True
    assert result["verified"] is False


def test_rpm_verifier_rejects_invalid_signature_even_if_unsigned_allowed(monkeypatch):
    from types import SimpleNamespace
    import core.security.rpm_verifier as verifier
    monkeypatch.setattr(verifier.shutil, "which", lambda name: "/usr/bin/rpmkeys")
    monkeypatch.setattr(verifier.subprocess, "run", lambda *a, **k: SimpleNamespace(
        returncode=1, stdout="package.rpm: digests OK; signatures NOT OK", stderr=""))
    result = verifier.verify_rpm_signature("package.rpm")
    assert result["unsigned"] is False
    assert result["verified"] is False


def test_rpm_verifier_classifies_spanish_digest_output_as_unsigned(monkeypatch):
    from types import SimpleNamespace
    import core.security.rpm_verifier as verifier
    monkeypatch.setattr(verifier.shutil, "which", lambda name: "/usr/bin/rpmkeys")
    monkeypatch.setattr(verifier.subprocess, "run", lambda *a, **k: SimpleNamespace(
        returncode=0,
        stdout=("Header SHA256 resumen: OK\nPayload SHA256 resumen: OK"),
        stderr=""))
    result = verifier.verify_rpm_signature("package.rpm")
    assert result["unsigned"] is True
    assert result["digest_ok"] is True
    assert result["verified"] is False


def test_rpm_verifier_rejects_spanish_bad_digest_output(monkeypatch):
    from types import SimpleNamespace
    import core.security.rpm_verifier as verifier
    monkeypatch.setattr(verifier.shutil, "which", lambda name: "/usr/bin/rpmkeys")
    monkeypatch.setattr(verifier.subprocess, "run", lambda *a, **k: SimpleNamespace(
        returncode=1,
        stdout=("Header SHA256 resumen: OK\nPayload SHA256 resumen: BAD"),
        stderr=""))
    result = verifier.verify_rpm_signature("package.rpm")
    assert result["digest_ok"] is False
    assert result["unsigned"] is False
