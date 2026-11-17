"""Paso 5: seguridad y servicios del sistema."""

from gui.layouts import add_page
from gui.status import service_states
from PySide6.QtWidgets import QCheckBox, QGroupBox, QLabel, QVBoxLayout, QWidget

HELP = """
<p><b>Seguridad y servicios</b></p>
<p>El firewall queda habilitado por defecto y solo permite SSH. SSH permanece
deshabilitado salvo que lo actives expresamente. Si habilitás SSH sin
autenticación por contraseña, necesitás una clave pública instalada de antemano.</p>
<p><code>kioskuser</code> puede usar <code>sudo</code> pidiendo contraseña.
La opción <code>NOPASSWD</code> es avanzada y reduce la seguridad. También podés
bloquear las consolas virtuales para que no haya login local.</p>
<p>Los estados de <code>firewalld</code> y <code>sshd</code> corresponden al equipo
donde corre Creador Personalizado, no a la ISO que se está construyendo.</p>
"""


class SecurityTabMixin:
    """Paso 5: seguridad y servicios (mixin de KioskBuilderGUI)."""

    def init_tab_security(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        group_net = QGroupBox("Protección de red y acceso remoto")
        net_layout = QVBoxLayout(group_net)
        self.check_firewall = QCheckBox("Habilitar firewall del sistema")
        self.check_firewall.setChecked(True)
        self.check_firewall.setToolTip(
            "Activa firewalld y permite solo SSH. Recomendado para equipos conectados a la red."
        )
        self.check_enable_ssh = QCheckBox("Habilitar administración remota por SSH")
        self.check_enable_ssh.setChecked(False)
        self.check_enable_ssh.setToolTip(
            "SSH permanece deshabilitado por defecto. Activá esta opción solo si necesitás acceso remoto."
        )
        self.check_ssh_password = QCheckBox(
            "Permitir autenticación SSH con contraseña (menos seguro)"
        )
        self.check_ssh_password.setChecked(False)
        self.check_ssh_password.setEnabled(False)
        self.check_enable_ssh.toggled.connect(self._on_ssh_toggled)
        self.check_ssh_password.setToolTip(
            "Si se desactiva, necesitás una clave pública instalada previamente para acceder por SSH."
        )
        net_layout.addWidget(self.check_firewall)
        net_layout.addWidget(self.check_enable_ssh)
        net_layout.addWidget(self.check_ssh_password)

        self.lbl_service_state = QLabel("Consultando servicios del host…")
        self.lbl_service_state.setObjectName("managerStatus")
        self.lbl_service_state.setWordWrap(True)
        net_layout.addWidget(self.lbl_service_state)

        group_admin = QGroupBox("Privilegios y acceso local")
        admin_layout = QVBoxLayout(group_admin)
        self.check_sudo_nopasswd = QCheckBox(
            "Permitir sudo sin contraseña para wheel (menos seguro)"
        )
        self.check_sudo_nopasswd.setChecked(False)
        self.check_sudo_nopasswd.setToolTip(
            "Por defecto sudo pide la contraseña de kioskuser. Activá esta opción solo si automatizás tareas administrativas."
        )
        self.check_vt = QCheckBox(
            "Bloquear consolas virtuales (deshabilita getty en tty2…tty6)"
        )
        self.check_vt.setChecked(True)
        self.check_vt.setToolTip(
            "Desactiva los getty y el auto-spawn de VTs. No elimina el cambio de VT a nivel kernel."
        )
        admin_layout.addWidget(self.check_sudo_nopasswd)
        admin_layout.addWidget(self.check_vt)

        note = QLabel(
            "root permanece bloqueado. La administración se realiza con kioskuser y sudo. "
            "Los estados consultados son los servicios del host de compilación."
        )
        note.setObjectName("inlineHint")
        note.setWordWrap(True)
        layout.addWidget(group_net)
        layout.addWidget(group_admin)
        layout.addWidget(note)
        layout.addStretch(1)

        self._register_advanced(self.check_ssh_password)
        self._register_advanced(group_admin)
        add_page(
            self, "step5", tab, "Seguridad y servicios",
            "Configurá la superficie de acceso, los privilegios y los servicios del sistema.",
            HELP, step=5,
        )
        self.refresh_service_state()

    def _on_ssh_toggled(self, enabled):
        self.check_ssh_password.setEnabled(enabled)
        if not enabled:
            self.check_ssh_password.setChecked(False)

    def refresh_service_state(self):
        """Actualiza el estado del host sin bloquear el hilo de la interfaz."""
        start = getattr(self, "_start_host_status_query", None)
        if callable(start):
            start(force=True)
            return
        states = service_states()
        self.lbl_service_state.setText(
            "Servicios del host: " + " · ".join(
                f"{name}: {state}" for name, state in states.items()
            )
        )
