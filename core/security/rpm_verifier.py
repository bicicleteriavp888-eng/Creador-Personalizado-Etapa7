"""Verificación de firmas y digests de RPM locales."""
import re
import shutil
import subprocess


def _digest_status(output):
    """Detecta digests válidos en salidas de rpm en inglés y español."""
    low = (output or "").casefold()
    # Un error explícito prevalece sobre cualquier indicación positiva.
    bad = (
        "digests not ok", "digest not ok", "digests nok",
        "resumen: incorrecto", "resumen: no", "digest: bad",
        "digests: bad", "payload digest: bad", "header digest: bad",
        "not verified", "no verificado",
    )
    if any(marker in low for marker in bad):
        return False

    # Salida habitual de RPM en inglés: "digests OK" / "digests signatures OK".
    if re.search(r"\bdigests?(?:\s+signatures)?\s+ok\b", low):
        return True

    # Salida localizada de Fedora: "Header SHA256 resumen: OK".
    digest_lines = [
        line for line in low.splitlines()
        if re.search(r"(sha\d+|digest|resumen)", line)
    ]
    if digest_lines:
        return all(re.search(r"\bok\s*$", line) for line in digest_lines)

    return False


def verify_rpm_signature(rpm_path):
    """Clasifica RPM como firmado/confiable, sin firma o inválido.

    La aceptación de RPM sin firma se decide en el Builder, nunca aquí.
    Una firma presente pero no verificable y un digest incorrecto siempre fallan.
    """
    if not rpm_path:
        return {"signed": False, "verified": False, "trusted": False,
                "unsigned": False, "digest_ok": False, "error": "Ruta RPM vacía."}
    tool = shutil.which("rpmkeys") or shutil.which("rpm")
    if not tool:
        return {"signed": False, "verified": False, "trusted": False,
                "unsigned": False, "digest_ok": False,
                "error": "No está instalado rpmkeys/rpm para verificar firmas."}
    cmd = ([tool, "--checksig", "--verbose", rpm_path] if tool.endswith("rpmkeys")
           else [tool, "-K", "--verbose", rpm_path])
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=20,
                             stdin=subprocess.DEVNULL)
        output = ((res.stdout or "") + "\n" + (res.stderr or "")).strip()
        low = output.casefold()
        digest_ok = _digest_status(output)
        signature_markers = ("signature", "firma", "pgp", "gpg")
        has_signature = any(marker in low for marker in signature_markers)
        bad_markers = ("nokey", "not trusted", "nottrusted", "not ok",
                       "bad signature", "signatures not ok", "signature not ok",
                       "firma incorrecta", "firma no válida", "firma no valida")
        bad_signature = has_signature and any(marker in low for marker in bad_markers)
        trusted = res.returncode == 0 and digest_ok and has_signature and not bad_signature
        unsigned = res.returncode == 0 and digest_ok and not has_signature
        if trusted:
            error = ""
        elif unsigned:
            error = "El RPM no contiene firma digital; sus digests son correctos."
        elif not digest_ok:
            error = "El RPM tiene digests incorrectos o no verificables."
        else:
            error = "La firma RPM existe, pero no es válida o la clave no es de confianza."
        return {"signed": has_signature, "verified": trusted, "trusted": trusted,
                "unsigned": unsigned, "digest_ok": digest_ok,
                "signature": output, "error": error}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"signed": False, "verified": False, "trusted": False,
                "unsigned": False, "digest_ok": False, "error": str(exc)}
