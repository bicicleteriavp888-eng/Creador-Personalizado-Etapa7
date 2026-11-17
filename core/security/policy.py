"""Politicas de seguridad que se traducen al Kickstart."""


def firewall_line(enable_firewall, enable_ssh):
    """Directiva ``firewall`` del Kickstart."""
    if not enable_firewall:
        return "firewall --disabled"
    suffix = " --service=ssh" if enable_ssh else ""
    return "firewall --enabled" + suffix


def enabled_services(enable_ssh, enable_firewall, base="NetworkManager,seatd"):
    """Servicios que systemd habilita en la imagen."""
    services = base
    if enable_ssh:
        services += ",sshd"
    if enable_firewall:
        services += ",firewalld"
    return services


def admin_packages(enable_firewall, enable_ssh):
    """Paquetes de administracion y servicios de red."""
    packages = ["sudo"]
    if enable_firewall:
        packages.append("firewalld")
    if enable_ssh:
        packages.extend(["openssh-server", "openssh-clients"])
    return packages


def sudoers_line(sudo_nopasswd):
    """Regla de sudo para el grupo wheel."""
    if sudo_nopasswd:
        return "%wheel ALL=(ALL) NOPASSWD: ALL"
    return "%wheel ALL=(ALL) ALL"


def ssh_post_block(enable_ssh, ssh_password_auth):
    """Script que configura y habilita sshd solo si el usuario lo pidio."""
    if not enable_ssh:
        return ""
    password = "yes" if ssh_password_auth else "no"
    return f"""
# --- SSH: habilitado de forma explicita por el usuario ---
mkdir -p /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/00-kiosk.conf <<'KIOSK_EOF'
PasswordAuthentication {password}
KbdInteractiveAuthentication {password}
PermitRootLogin no
KIOSK_EOF
systemctl enable sshd.service >/dev/null 2>&1
"""


def firewall_post_block(enable_firewall, enable_ssh):
    """Script que habilita firewalld y solo abre SSH si corresponde."""
    if not enable_firewall:
        return ""
    ssh_rule = (
        "firewall-offline-cmd --zone=public --add-service=ssh "
        ">/dev/null 2>&1 || true"
        if enable_ssh
        else ": # SSH deshabilitado por defecto"
    )
    return f"""
# --- Firewall: solo los servicios explicitamente habilitados ---
systemctl enable firewalld.service >/dev/null 2>&1
if command -v firewall-offline-cmd >/dev/null 2>&1; then
    {ssh_rule}
fi
"""
