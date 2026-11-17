"""Validador estructural de ISOs para Creador-kiosk 2.0 (Laboratorio)."""

import os
from core.iso.iso_inspector import inspect_iso_metadata
from core.kickstart.validator import validate_kickstart_content


def validate_iso_package(iso_path, ks_content=None, required_boot_modes=("bios", "uefi")):
    """Realiza validación completa (básica, estructural y kickstart) de una ISO."""
    results = {
        "exists": False,
        "valid_size": False,
        "sha256": None,
        "bios_compatible": False,
        "uefi_compatible": False,
        "kickstart_valid": True,
        "errors": [],
        "warnings": [],
    }

    if not os.path.exists(iso_path):
        results["errors"].append(f"La ISO no existe en la ruta: {iso_path}")
        return results

    results["exists"] = True
    meta = inspect_iso_metadata(iso_path)
    if "error" in meta:
        results["errors"].append(meta["error"])
        return results

    results["sha256"] = meta.get("sha256")
    results["valid_size"] = meta.get("size_bytes", 0) > 1024 * 1024 * 50  # > 50 MB
    results["bios_compatible"] = meta.get("has_isolinux", False)
    results["uefi_compatible"] = meta.get("has_efi", False)

    if not results["valid_size"]:
        results["warnings"].append("El tamaño de la ISO es inusualmente pequeño.")

    required = {str(mode).lower() for mode in (required_boot_modes or ())}
    if "bios" in required and not results["bios_compatible"]:
        results["errors"].append("No se detectó entrada de arranque BIOS/El Torito.")
    if "uefi" in required and not results["uefi_compatible"]:
        results["errors"].append("No se detectó imagen de arranque UEFI/EFI.")

    if ks_content:
        ks_issues = validate_kickstart_content(ks_content)
        for itype, msg in ks_issues:
            if itype == "error":
                results["kickstart_valid"] = False
                results["errors"].append(f"Kickstart: {msg}")
            else:
                results["warnings"].append(f"Kickstart: {msg}")

    return results
