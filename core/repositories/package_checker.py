"""Comprobaciones de nombres de paquetes, validez y existencia en repositorios."""

import re
import shutil
import subprocess

PACKAGE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*")


def split_package_names(raw):
    """Separa una lista de paquetes escrita con espacios o comas."""
    return [pkg for pkg in re.split(r"[\s,]+", raw or "") if pkg]


def invalid_package_names(raw):
    """Devuelve los nombres de paquete no validos de una lista separada."""
    return [
        pkg
        for pkg in split_package_names(raw)
        if pkg and not PACKAGE_RE.fullmatch(pkg)
    ]


def validate_product_name(value):
    """Valida el nombre de producto usado en /etc/os-release y branding."""
    value = (value or "").strip()
    if len(value) > 80:
        return "El nombre del producto admite hasta 80 caracteres."
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        return (
            "El nombre del producto no puede contener caracteres de control "
            "ni saltos de linea."
        )
    if '"' in value or "\\" in value or "$" in value:
        return (
            "El nombre del producto no puede contener comillas dobles, "
            "barras invertidas ni el caracter $."
        )
    return None


def check_package_exists(pkg_name):
    """Comprueba si un paquete existe en los repositorios del sistema usando dnf repoquery.

    Si dnf no está disponible o falla, devuelve True (para no bloquear en entornos sin dnf),
    pero si dnf repoquery confirma que no existe, devuelve False.
    """
    pkg_name = (pkg_name or "").strip()
    if not pkg_name or not PACKAGE_RE.fullmatch(pkg_name):
        return False

    dnf_bin = shutil.which("dnf")
    if not dnf_bin:
        # Si no hay dnf en el host (ej. contenedor o sistema sin DNF), asumimos válido
        return True

    try:
        res = subprocess.run(
            [dnf_bin, "-q", "repoquery", "--installed", "--available", pkg_name],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if res.returncode == 0 and res.stdout.strip():
            return True
        # Intentar también con dnf info si repoquery es estricto
        res_info = subprocess.run(
            [dnf_bin, "-q", "info", pkg_name],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if res_info.returncode == 0 and pkg_name in res_info.stdout:
            return True
        return False
    except Exception:
        # En caso de timeout o error de red/repos, no bloquear preventivamente
        return True
