"""Generador de informes de laboratorio y diagnóstico para Creador-kiosk 2.0."""

import time
from html import escape


def generate_txt_report(validation_data):
    """Genera un informe en formato texto plano a partir de los datos de validación."""
    lines = [
        "==================================================",
        "INFORME DE LABORATORIO ISO — CREADOR-KIOSK 2.0",
        f"Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "==================================================",
        f"Ruta ISO: {validation_data.get('path', 'N/A')}",
        f"Tamaño (MB): {validation_data.get('size_mb', 'N/A')}",
        f"SHA-256: {validation_data.get('sha256', 'N/A')}",
        f"Compatible BIOS: {validation_data.get('bios_compatible', False)}",
        f"Compatible UEFI: {validation_data.get('uefi_compatible', False)}",
        f"Kickstart Válido: {validation_data.get('kickstart_valid', True)}",
        f"Estado: {validation_data.get('status', 'GENERATED')}",
        "",
        "--- PRUEBAS QEMU ---",
    ]
    qemu = validation_data.get("qemu", {})
    if qemu:
        for mode, result in qemu.items():
            lines.append(f"  {mode.upper()}: {result.get('status', 'UNKNOWN')} — marcadores: {', '.join(result.get('boot_markers', [])) or 'ninguno'}")
    else:
        lines.append("  No ejecutadas.")
    lines.extend(["", "--- ERRORES ---"])
    errors = validation_data.get("errors", [])
    if errors:
        for err in errors:
            lines.append(f"  [X] {err}")
    else:
        lines.append("  Ninguno.")

    lines.append("")
    lines.append("--- ADVERTENCIAS ---")
    warnings = validation_data.get("warnings", [])
    if warnings:
        for warn in warnings:
            lines.append(f"  [!] {warn}")
    else:
        lines.append("  Ninguna.")

    lines.append("==================================================")
    return "\n".join(lines)


def generate_html_report(validation_data):
    """Genera un informe en formato HTML a partir de los datos de validación."""
    txt = generate_txt_report(validation_data)
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Informe de Laboratorio ISO - Creador-kiosk 2.0</title>
<style>
body {{ font-family: sans-serif; margin: 2rem; background: #f4f6f9; color: #333; }}
.container {{ background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
pre {{ background: #f8f9fa; padding: 1rem; border-radius: 4px; border: 1px solid #dee2e6; }}
h1 {{ color: #0066cc; }}
</style>
</head>
<body>
<div class="container">
<h1>Informe de Laboratorio ISO</h1>
<pre>{escape(txt)}</pre>
</div>
</body>
</html>
"""
    return html
