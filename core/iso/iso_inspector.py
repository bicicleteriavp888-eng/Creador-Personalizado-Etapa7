"""Inspección de metadatos y catálogo El Torito de imágenes ISO."""
import hashlib
import os
import shutil
import subprocess


def calculate_sha256(iso_path):
    digest = hashlib.sha256()
    with open(iso_path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_iso_metadata(iso_path):
    if not os.path.isfile(iso_path):
        return {"error": "El archivo ISO no existe o no es un archivo regular."}
    stat = os.stat(iso_path)
    result = {
        "path": os.path.abspath(iso_path), "size_bytes": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "sha256": calculate_sha256(iso_path), "has_efi": False,
        "has_isolinux": False, "has_el_torito": False,
        "inspection_tool": None, "status": "GENERATED",
    }
    xorriso = shutil.which("xorriso")
    if xorriso:
        try:
            proc = subprocess.run([xorriso, "-indev", iso_path, "-report_el_torito", "as_mkisofs"],
                                  capture_output=True, text=True, timeout=30)
            output = (proc.stdout or "") + "\n" + (proc.stderr or "")
            if proc.returncode == 0:
                result["inspection_tool"] = "xorriso"
                result["has_el_torito"] = "-b " in output or "-e " in output
                result["has_isolinux"] = "-b " in output
                result["has_efi"] = "-e " in output or "efi" in output.lower() and "boot" in output.lower()
        except (OSError, subprocess.TimeoutExpired):
            pass
    if result["inspection_tool"] is None:
        isoinfo = shutil.which("isoinfo")
        if isoinfo:
            try:
                proc = subprocess.run([isoinfo, "-d", "-i", iso_path], capture_output=True,
                                      text=True, timeout=20)
                if proc.returncode == 0:
                    result["inspection_tool"] = "isoinfo"
                    out = proc.stdout.lower()
                    result["has_el_torito"] = "eltorito" in out or "boot catalog" in out
                    result["has_isolinux"] = result["has_el_torito"]
                    result["has_efi"] = "efi" in out
            except (OSError, subprocess.TimeoutExpired):
                pass
    if result["inspection_tool"] is None:
        result["inspection_warning"] = "Instale xorriso o genisoimage para inspeccionar El Torito."
    return result
