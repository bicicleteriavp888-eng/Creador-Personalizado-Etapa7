"""Auditoría estructural rápida de ISO Fedora sin arrancar una VM.

No instala ni modifica nada. Extrae únicamente los archivos de configuración
GRUB y las imágenes squashfs encontradas, en un directorio temporal.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def _run(command: list[str], timeout: int = 45) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout,
                          check=False, env={**os.environ, "LC_ALL": "C"})


def _run_listing(command: list[str], output_path: Path, timeout: int = 180) -> tuple[int, str, int]:
    """Ejecuta unsquashfs enviando el listado a disco, no a memoria RAM."""
    with output_path.open("w", encoding="utf-8", errors="replace") as output:
        proc = subprocess.run(command, stdout=output, stderr=subprocess.PIPE, text=True,
                              timeout=timeout, check=False,
                              env={**os.environ, "LC_ALL": "C"})
    with output_path.open("r", encoding="utf-8", errors="replace") as listing:
        entries = sum(1 for line in listing if line.strip())
    return proc.returncode, proc.stderr or "", entries


def _iso_paths(xorriso: str, iso: str) -> tuple[list[str], list[str]]:
    proc = _run([xorriso, "-indev", iso, "-find", "/", "-type", "f", "-exec", "lsdl"], 90)
    if proc.returncode:
        raise RuntimeError((proc.stderr or proc.stdout or "xorriso no pudo leer el catálogo ISO")[-3000:])
    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    paths = set(re.findall(r"(?<![\w.])(/[A-Za-z0-9_./+@=-]+)", output))
    grub = sorted(p for p in paths if p.lower().endswith("grub.cfg"))
    squash = sorted(p for p in paths if Path(p).name.lower() == "squashfs.img")
    return grub, squash


def _extract(xorriso: str, iso: str, iso_path: str, destination: Path) -> None:
    proc = _run([xorriso, "-osirrox", "on", "-indev", iso, "-extract", iso_path, str(destination)], 120)
    if proc.returncode or not destination.is_file():
        raise RuntimeError((proc.stderr or proc.stdout or f"No se pudo extraer {iso_path}")[-2000:])


def audit_iso_quick(iso_path: str) -> dict:
    """Audita catálogo ISO, sintaxis GRUB y metadatos squashfs.

    ``status`` solo puede ser PASS, WARN, FAIL o UNAVAILABLE. PASS significa
    que las comprobaciones disponibles finalizaron correctamente, no que la
    ISO haya arrancado ni que el sistema instalado funcione.
    """
    iso = Path(iso_path).expanduser().resolve()
    report = {
        "path": str(iso), "status": "UNAVAILABLE", "checks": [],
        "errors": [], "warnings": [], "grub_configs": [], "squashfs_images": [],
    }
    if not iso.is_file():
        report["status"] = "FAIL"
        report["errors"].append(f"No existe un archivo ISO en: {iso}")
        return report
    xorriso, grub_checker, unsquashfs = (
        shutil.which("xorriso"), shutil.which("grub2-script-check") or shutil.which("grub-script-check"),
        shutil.which("unsquashfs"),
    )
    if not xorriso:
        report["warnings"].append("xorriso no está instalado; no se puede inspeccionar el catálogo ISO.")
        report["status"] = "UNAVAILABLE"
        return report
    try:
        grub_paths, squash_paths = _iso_paths(xorriso, str(iso))
        report["checks"].append({"name": "catálogo ISO", "status": "PASS"})
        if not grub_paths:
            report["warnings"].append("No se encontraron archivos grub.cfg en el catálogo ISO.")
        if not squash_paths:
            report["warnings"].append("No se encontró squashfs.img; puede ser una ISO que no use LiveOS squashfs.")
        with tempfile.TemporaryDirectory(prefix="creador-iso-audit-") as tmp:
            root = Path(tmp)
            for index, member in enumerate(grub_paths):
                if not grub_checker:
                    report["warnings"].append("grub2-script-check no está instalado; se omitió la validación sintáctica GRUB.")
                    break
                local = root / f"grub-{index}.cfg"
                _extract(xorriso, str(iso), member, local)
                check = _run([grub_checker, str(local)], 20)
                item = {"path": member, "status": "PASS" if check.returncode == 0 else "FAIL",
                        "detail": (check.stderr or check.stdout or "Sintaxis aceptada.")[-2000:]}
                report["grub_configs"].append(item)
                if check.returncode:
                    report["errors"].append(f"GRUB inválido en {member}: {item['detail']}")
            if grub_paths and grub_checker:
                report["checks"].append({"name": "sintaxis GRUB", "status": "FAIL" if any(x["status"] == "FAIL" for x in report["grub_configs"]) else "PASS"})
            for index, member in enumerate(squash_paths):
                if not unsquashfs:
                    report["warnings"].append("unsquashfs no está instalado; se omitió la auditoría de squashfs.img.")
                    break
                local = root / f"squashfs-{index}.img"
                _extract(xorriso, str(iso), member, local)
                listing_path = root / f"squashfs-{index}.listing.txt"
                returncode, detail, entries = _run_listing(
                    [unsquashfs, "-ll", "-no-progress", str(local)], listing_path, 180
                )
                item = {"path": member, "size_bytes": local.stat().st_size,
                        "status": "PASS" if returncode == 0 else "FAIL",
                        "listed_entries": entries}
                report["squashfs_images"].append(item)
                if returncode:
                    report["errors"].append(f"No se pudo listar {member}: {detail[-2000:]}")
            if squash_paths and unsquashfs:
                report["checks"].append({"name": "integridad/listado squashfs", "status": "FAIL" if any(x["status"] == "FAIL" for x in report["squashfs_images"]) else "PASS"})
    except (OSError, subprocess.TimeoutExpired, RuntimeError) as exc:
        report["errors"].append(str(exc))
    report["status"] = "FAIL" if report["errors"] else ("WARN" if report["warnings"] else "PASS")
    return report
