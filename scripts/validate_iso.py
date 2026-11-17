#!/usr/bin/env python3
"""Valida una ISO y, opcionalmente, intenta arrancarla con QEMU.

No escribe discos físicos: QEMU usa snapshot y no se conecta ningún disco host.
Un arranque iniciado no equivale a instalación funcional; requiere revisión humana.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import tempfile
import shutil as _shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.validation.iso_validator import validate_iso_package
from core.validation.report_generator import generate_txt_report


def find_ovmf():
    code_candidates = [
        "/usr/share/edk2/ovmf/OVMF_CODE.fd",
        "/usr/share/edk2/ovmf/OVMF_CODE.secboot.fd",
        "/usr/share/OVMF/OVMF_CODE.fd",
        "/usr/share/qemu/OVMF_CODE.fd",
    ]
    vars_candidates = [
        "/usr/share/edk2/ovmf/OVMF_VARS.fd",
        "/usr/share/OVMF/OVMF_VARS.fd",
        "/usr/share/qemu/OVMF_VARS.fd",
    ]
    code = next((p for p in code_candidates if os.path.isfile(p)), None)
    variables = next((p for p in vars_candidates if os.path.isfile(p)), None)
    return (code, variables) if code and variables else None


def qemu_boot(iso, firmware=None, timeout=75, memory=2048):
    qemu = shutil.which("qemu-system-x86_64")
    if not qemu:
        return {"available": False, "status": "NOT_AVAILABLE", "detail": "qemu-system-x86_64 no instalado"}
    cmd = [qemu, "-m", str(memory), "-smp", "2", "-cdrom", str(iso),
           "-boot", "d", "-snapshot", "-no-reboot", "-no-shutdown",
           "-display", "none", "-monitor", "none", "-nic", "none", "-serial", "stdio"]
    temp = tempfile.TemporaryDirectory(prefix="ck-ovmf-") if firmware else None
    try:
        if firmware:
            code, vars_template = firmware
            vars_copy = os.path.join(temp.name, "OVMF_VARS.fd")
            _shutil.copyfile(vars_template, vars_copy)
            cmd += ["-drive", f"if=pflash,format=raw,readonly=on,file={code}",
                    "-drive", f"if=pflash,format=raw,file={vars_copy}"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, errors="replace", start_new_session=True)
        try:
            output, _ = proc.communicate(timeout=timeout)
            status = "EXITED"
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                output, _ = proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill(); output, _ = proc.communicate()
            status = "RUNNING_AT_TIMEOUT"
        markers = ("Linux version", " dracut", "Starting", "Anaconda", "login:")
        observed = [marker for marker in markers if marker.lower() in output.lower()]
        return {"available": True, "status": status, "returncode": proc.returncode,
                "boot_markers": observed, "detail": output[-12000:]}
    except OSError as exc:
        return {"available": False, "status": "ERROR", "detail": str(exc)}
    finally:
        if temp:
            temp.cleanup()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("iso")
    parser.add_argument("--kickstart")
    parser.add_argument("--boot-mode", choices=("dual", "uefi"), default="dual",
                        help="Modos requeridos por la configuración de la ISO")
    parser.add_argument("--qemu", action="store_true", help="Intenta arranque BIOS y UEFI")
    parser.add_argument("--timeout", type=int, default=75)
    parser.add_argument("--report-dir", default="./laboratory-reports")
    args = parser.parse_args()
    iso = Path(args.iso).expanduser().resolve()
    ks = Path(args.kickstart).read_text(encoding="utf-8") if args.kickstart else None
    validation = validate_iso_package(str(iso), ks, ("bios", "uefi") if args.boot_mode == "dual" else ("uefi",))
    validation["status"] = "VALIDATED" if not validation["errors"] and validation["bios_compatible"] else "GENERATED"
    validation["path"] = str(iso)
    validation["size_mb"] = round(iso.stat().st_size / 1048576, 2) if iso.is_file() else 0
    validation["qemu"] = {}
    if args.qemu and validation.get("exists"):
        validation["qemu"]["bios"] = qemu_boot(iso, timeout=args.timeout)
        ovmf = find_ovmf()
        validation["qemu"]["uefi"] = qemu_boot(iso, firmware=ovmf, timeout=args.timeout) if ovmf else {
            "available": False, "status": "NOT_AVAILABLE", "detail": "Firmware OVMF no encontrado"}
        boot_results = validation["qemu"]
        expected = ["uefi"] if args.boot_mode == "uefi" else ["bios", "uefi"]
        all_observed = all(
            boot_results.get(mode, {}).get("available")
            and bool(boot_results.get(mode, {}).get("boot_markers"))
            for mode in expected
        )
        validation["status"] = "TESTED" if all_observed and not validation["errors"] else "BOOT_TEST_INCOMPLETE"
    out = Path(args.report_dir).expanduser().resolve(); out.mkdir(parents=True, exist_ok=True)
    stem = iso.stem
    (out / f"{stem}-report.json").write_text(json.dumps(validation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / f"{stem}-report.txt").write_text(generate_txt_report(validation), encoding="utf-8")
    print(json.dumps(validation, indent=2, ensure_ascii=False))
    # BIOS / UEFI no presentes deben fallar de forma explícita, nunca simular OK.
    return 0 if not validation.get("errors") else 2

if __name__ == "__main__":
    raise SystemExit(main())
