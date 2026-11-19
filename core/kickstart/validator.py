"""Validación estática y con pykickstart de recetas Kickstart."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path


def validate_kickstart_content(ks_text: str) -> list[tuple[str, str]]:
    """Comprueba estructura básica sin sustituir al validador oficial."""
    issues: list[tuple[str, str]] = []
    if not ks_text or not ks_text.strip():
        return [("error", "El contenido Kickstart está vacío.")]
    lines = [line.strip() for line in ks_text.splitlines()]
    directives = {line.split()[0] for line in lines if line and not line.startswith("#") and not line.startswith("%")}
    if "text" not in directives and "graphical" not in directives:
        issues.append(("warning", "No se encontró 'text' ni 'graphical'."))
    if "bootloader" not in directives:
        issues.append(("error", "Falta la directiva 'bootloader'."))
    if "%packages" not in lines:
        issues.append(("error", "Falta la sección '%packages'."))
    elif "%end" not in lines[lines.index("%packages") + 1:]:
        issues.append(("error", "La sección '%packages' no tiene su %end."))
    section_starts = (
        "%packages", "%post", "%pre", "%pre-install", "%onerror",
        "%traceback", "%addon",
    )
    for index, line in enumerate(lines):
        if line.startswith(section_starts):
            next_section = next(
                (position for position in range(index + 1, len(lines))
                 if lines[position].startswith(section_starts)),
                len(lines),
            )
            if "%end" not in lines[index + 1:next_section]:
                issues.append(("error", f"La sección '{line.split()[0]}' iniciada en la línea {index + 1} no tiene %end."))
    if not any(line.startswith("%post") for line in lines):
        issues.append(("warning", "No se encontró una sección '%post'."))
    if not re.search(r"(?m)^part\s+/\s", ks_text):
        if not re.search(r"(?m)^autopart(?:\s|$)", ks_text):
            issues.append(("warning", "No se encontró particionamiento root explícito ni 'autopart'."))
    for index, line in enumerate(lines, 1):
        if line.startswith("%") and line not in {"%packages", "%end"} and not line.startswith(("%post", "%pre", "%onerror", "%traceback", "%pre-install", "%addon", "%include")):
            issues.append(("warning", f"Línea {index}: sección Kickstart no reconocida por el validador básico: {line.split()[0]}"))
    return issues


def validate_kickstart_file(path: str | Path, release: str = "44") -> dict:
    """Ejecuta ksvalidator y conserva un fallback estático explícito.

    La ausencia de ksvalidator se informa como advertencia; nunca se etiqueta
    como validación oficial satisfactoria.
    """
    target = Path(path)
    if not target.is_file():
        return {"ok": False, "validator": "none", "issues": [("error", f"No existe Kickstart: {target}")]}
    content = target.read_text(encoding="utf-8", errors="replace")
    issues = validate_kickstart_content(content)
    binary = shutil.which("ksvalidator")
    if not binary:
        issues.append(("warning", "ksvalidator no está instalado; se ejecutó solo la validación estructural interna. Instala python3-pykickstart."))
        return {"ok": not any(kind == "error" for kind, _ in issues), "validator": "internal", "issues": issues, "official": False}
    version = str(release or "44")
    if version.isdigit():
        version = f"F{version}"
    try:
        result = subprocess.run(
            [binary, "-v", version, str(target)],
            capture_output=True, text=True, timeout=30,
            stdin=subprocess.DEVNULL, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        issues.append(("error", f"No se pudo ejecutar ksvalidator: {exc}"))
        return {"ok": False, "validator": "ksvalidator", "issues": issues, "official": False}
    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    if result.returncode:
        issues.append(("error", output or f"ksvalidator terminó con código {result.returncode}."))
    elif output:
        issues.append(("warning", output))
    return {"ok": result.returncode == 0 and not any(k == "error" for k, _ in issues),
            "validator": "ksvalidator", "issues": issues, "official": result.returncode == 0}
