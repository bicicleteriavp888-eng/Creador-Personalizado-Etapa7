"""Generacion del hash de contrasena para el Kickstart."""

import subprocess


def validate_initial_password(password):
    """Valida una contrasena inicial no vacia y apta para passwd/openssl.

    Se aceptan contrasenas cortas porque se fuerza su cambio en el primer
    inicio de sesion interactivo del sistema Live/instalado.
    """
    if password is None or str(password) == "":
        raise RuntimeError("La contrasena inicial de kioskuser no puede estar vacia.")
    password = str(password)
    if len(password) > 128 or any(ord(ch) < 32 or ord(ch) == 127 for ch in password):
        raise RuntimeError(
            "La contrasena debe tener como maximo 128 caracteres y no contener "
            "caracteres de control ni saltos de linea."
        )
    return password


def password_hash(password):
    """Devuelve el hash SHA-512 de la contrasena inicial usando openssl."""
    password = validate_initial_password(password)
    result = subprocess.run(
        ["openssl", "passwd", "-6", "-stdin"],
        input=password + "\n",
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip()
    if result.returncode != 0 or not value.startswith("$6$"):
        raise RuntimeError(
            "openssl no pudo generar un hash SHA512 valido: "
            + (result.stderr or "").strip()
        )
    return value
