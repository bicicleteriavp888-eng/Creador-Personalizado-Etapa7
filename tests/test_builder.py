import base64
import os
import re
import select
import signal
import subprocess
import tempfile
import threading

import pytest

from core.builder import KioskISOBuilder, invalid_package_names, validate_product_name


def _make_builder(tmpdir, **overrides):
    config = {
        "iso_name": "TestKiosk",
        "version": "1.0",
        "developer": "Tester",
        "release": "44",
        "boot_mode": "uefi",
        "app_mode": "chromium",
        "app_url": "http://example.com",
        "password": "test-password",
        "output_dir": tmpdir,
    }
    config.update(overrides)
    builder = KioskISOBuilder(config)
    builder.work_dir = tmpdir
    builder.ks_path = os.path.join(tmpdir, "kiosk.ks")
    return builder


def test_installer_section_generation():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy banner image
        banner_path = os.path.join(tmpdir, "banner.png")
        with open(banner_path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 20)

        config = {
            "iso_name": "TestKiosk",
            "version": "1.0",
            "developer": "Tester",
            "release": "44",
            "boot_mode": "uefi",
            "app_mode": "chromium",
            "app_url": "http://example.com",
            "installer_banner": banner_path,
            "installer_text": "Bienvenidos al instalador de TestKiosk",
            "output_dir": tmpdir,
        }

        builder = KioskISOBuilder(config)
        builder.work_dir = tmpdir
        builder.ks_path = os.path.join(tmpdir, "kiosk.ks")

        section = builder._installer_section()
        assert "/usr/share/anaconda/pixmaps" in section
        assert "top-banner.png" in section
        assert "Bienvenidos al instalador de TestKiosk" in section
        assert "/etc/kiosk-installer-message.txt" in section


def test_enable_installer_packages():
    config_enabled = {
        "iso_name": "TestKiosk",
        "enable_installer": True,
        "app_mode": "chromium",
    }
    builder_enabled = KioskISOBuilder(config_enabled)
    app = builder_enabled._resolve_app()
    pkgs_enabled = builder_enabled._package_lines(app)
    assert "anaconda" in pkgs_enabled
    assert "anaconda-live" in pkgs_enabled
    # Anaconda 44 usa la interfaz web, que necesita Firefox.
    assert "firefox" in pkgs_enabled
    assert "polkit" in pkgs_enabled

    config_disabled = {
        "iso_name": "TestKiosk",
        "enable_installer": False,
        "app_mode": "chromium",
    }
    builder_disabled = KioskISOBuilder(config_disabled)
    pkgs_disabled = builder_disabled._package_lines(app)
    assert "anaconda" not in pkgs_disabled
    assert "firefox" not in pkgs_disabled


def test_cage_command_with_percent_is_not_in_execstart():
    with tempfile.TemporaryDirectory() as tmpdir:
        builder = _make_builder(
            tmpdir,
            app_url="http://example.com/a%20b",
        )
        exec_cmd = builder._resolve_app()["exec"]
        section = builder._cage_service_section(exec_cmd)

        assert "kiosk.mode=installer" in section
        exec_line = next(
            line for line in section.splitlines() if line.startswith("ExecStart=")
        )
        assert "/usr/local/bin/kiosk-app.cmd" in exec_line
        assert "%20" not in exec_line

        match = re.search(
            r"printf '%s' '([^']+)' \| base64 -d > "
            r"/usr/local/bin/kiosk-app\.cmd",
            section,
        )
        assert match, "No se encontro el script base64 de la app"
        decoded = base64.b64decode(match.group(1)).decode("utf-8")
        assert "http://example.com/a%20b" in decoded


def test_cage_description_escapes_percent():
    with tempfile.TemporaryDirectory() as tmpdir:
        builder = _make_builder(tmpdir, iso_name="Kiosk%20Test")
        section = builder._cage_service_section(
            builder._resolve_app()["exec"]
        )
        assert "Description=Kiosk Kiosk%%20Test" in section


def test_sway_uses_latam_keyboard_and_installer_mode():
    with tempfile.TemporaryDirectory() as tmpdir:
        builder = _make_builder(
            tmpdir,
            multi_app=True,
            app2_mode="chromium",
            app2_url="http://example.com/segunda",
        )
        app = builder._resolve_app()
        app2 = builder._resolve_app2()
        section = builder._sway_service_section(app["exec"], app2["exec"])

        assert "Environment=XKB_DEFAULT_LAYOUT=latam" in section
        assert "input type:keyboard xkb_layout latam" in section
        assert "kiosk.mode=installer" in section


def test_installer_boot_and_polkit_access():
    with tempfile.TemporaryDirectory() as tmpdir:
        builder = _make_builder(tmpdir, enable_installer=True)

        boot = builder._installer_boot_section()
        assert "%post --nochroot" in boot
        assert "isolinux/isolinux.cfg" in boot
        assert "EFI/BOOT/grub.cfg" in boot
        assert "kiosk.mode=installer" in boot
        assert "Instalar en disco (Anaconda)" in boot

        access = builder._installer_access_section()
        assert "org.fedoraproject.pkexec.liveinst" in access
        assert "kioskuser" in access
        assert "polkit.Result.YES" in access


def test_installer_boot_script_adds_bios_and_efi_entries():
    with tempfile.TemporaryDirectory() as tmpdir:
        builder = _make_builder(tmpdir, enable_installer=True)
        boot = builder._installer_boot_section()
        script = boot.replace("%post --nochroot", "", 1).replace("%end", "", 1)
        script_path = os.path.join(tmpdir, "installer-boot.sh")
        with open(script_path, "w", encoding="utf-8") as handle:
            handle.write(script)

        live_root = os.path.join(tmpdir, "live")
        os.makedirs(os.path.join(live_root, "isolinux"))
        os.makedirs(os.path.join(live_root, "EFI", "BOOT"))

        with open(
            os.path.join(live_root, "isolinux", "isolinux.cfg"),
            "w",
            encoding="utf-8",
        ) as handle:
            handle.write(
                "label linux0\n"
                "  menu label ^Start Test\n"
                "  kernel vmlinuz0\n"
                "  append initrd=initrd0.img root=live:LABEL=Test "
                "rootfstype=auto rhgb quiet\n"
                "menu end\n"
            )
        with open(
            os.path.join(live_root, "EFI", "BOOT", "grub.cfg"),
            "w",
            encoding="utf-8",
        ) as handle:
            handle.write(
                "menuentry 'Start Test' --class fedora {\n"
                "\tlinux /LiveOS/vmlinuz0 root=live:LABEL=Test "
                "rootfstype=auto rhgb quiet\n"
                "\tinitrd /LiveOS/initrd0.img\n"
                "}\n"
            )

        env = os.environ.copy()
        env["LIVE_ROOT"] = live_root
        result = subprocess.run(
            ["bash", script_path],
            env=env,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr

        with open(
            os.path.join(live_root, "isolinux", "isolinux.cfg"),
            encoding="utf-8",
        ) as handle:
            isolinux = handle.read()
        with open(
            os.path.join(live_root, "EFI", "BOOT", "grub.cfg"),
            encoding="utf-8",
        ) as handle:
            grub = handle.read()

        assert "label installer0" in isolinux
        assert "kiosk.mode=installer" in isolinux
        assert "Instalar en disco (Anaconda)" in grub
        assert "linux /LiveOS/vmlinuz0" in grub
        assert "kiosk.mode=installer" in grub


def test_installer_sections_empty_when_disabled():
    with tempfile.TemporaryDirectory() as tmpdir:
        builder = _make_builder(tmpdir, enable_installer=False)
        assert builder._installer_boot_section() == ""
        assert builder._installer_access_section() == ""


def test_kiosk_password_is_not_required_for_live_boot():
    builder = KioskISOBuilder(
        {"iso_name": "TestKiosk", "app_mode": "chromium", "password": ""}
    )
    assert builder._password_hash() == ""




def test_kiosk_account_is_locked_without_password_or_expiration():
    with tempfile.TemporaryDirectory() as tmpdir:
        builder = _make_builder(tmpdir, password="")
        assert builder._password_hash() == ""
        post = builder._post_base("")
        assert "usermod -L kioskuser" in post
        assert "chage --lastday 0 kioskuser" not in post
        assert "usermod -p" not in post


def test_chromium_sandbox_is_enabled_by_default():
    assert "--no-sandbox" not in KioskISOBuilder._chromium_exec("http://example.com")

    builder = KioskISOBuilder(
        {
            "iso_name": "TestKiosk",
            "app_mode": "chromium",
            "app_url": "http://example.com",
            "chromium_no_sandbox": True,
        }
    )
    assert "--no-sandbox" in builder._resolve_app()["exec"]


def test_security_toggles_in_kickstart():
    with tempfile.TemporaryDirectory() as tmpdir:
        builder = _make_builder(
            tmpdir,
            enable_installer=True,
            enable_firewall=True,
            enable_ssh=False,
            ssh_password_auth=False,
            sudo_nopasswd=False,
        )
        app = builder._resolve_app()
        pkgs = builder._package_lines(app)
        assert "firewalld" in pkgs

        builder._generate_kickstart(builder._password_hash())
        with open(builder.ks_path, encoding="utf-8") as handle:
            kickstart = handle.read()

        assert "firewall --enabled" in kickstart
        assert "firewall --enabled --service=ssh" not in kickstart
        assert "services --enabled=NetworkManager,seatd,firewalld" in kickstart
        assert "selinux --enforcing" in kickstart
        assert "sshd.service" not in kickstart
        assert "PasswordAuthentication no" not in kickstart
        assert "%wheel ALL=(ALL) ALL" in kickstart
        assert "NOPASSWD" not in kickstart
        assert "systemctl enable firewalld.service" in kickstart
        assert "%post --nochroot" in kickstart
        assert "kiosk.mode=installer" in kickstart
        assert "49-kiosk-liveinst.rules" in kickstart

        disabled = _make_builder(
            tmpdir,
            enable_installer=False,
            enable_firewall=False,
            enable_ssh=True,
            ssh_password_auth=True,
            sudo_nopasswd=True,
        )
        disabled_pkgs = disabled._package_lines(disabled._resolve_app())
        assert "firewalld" not in disabled_pkgs

        disabled._generate_kickstart(disabled._password_hash())
        with open(disabled.ks_path, encoding="utf-8") as handle:
            disabled_kickstart = handle.read()

        assert "firewall --disabled" in disabled_kickstart
        assert "PasswordAuthentication yes" in disabled_kickstart
        assert "sshd.service" in disabled_kickstart
        assert "firewall-offline-cmd --zone=public --add-service=ssh" not in disabled_kickstart
        assert "%wheel ALL=(ALL) NOPASSWD: ALL" in disabled_kickstart
        assert "49-kiosk-liveinst.rules" not in disabled_kickstart


def test_lightdm_is_removed_even_from_legacy_configuration():
    with tempfile.TemporaryDirectory() as tmpdir:
        builder = _make_builder(tmpdir, enable_lightdm=True)
        app = builder._resolve_app()
        pkgs = builder._package_lines(app)
        assert "lightdm" not in pkgs
        assert "python3-gobject" not in pkgs
        assert "gtk3" not in pkgs

        service = builder._cage_service_section(app["exec"])
        assert "systemctl enable kiosk.service" in service
        assert "systemctl set-default multi-user.target" in service
        assert "systemctl enable lightdm.service" not in service
        assert "PAMName=" not in service
        assert "User=kioskuser" in service
        assert "RuntimeDirectory=user/%U" in service
        assert "RuntimeDirectoryMode=0700" in service
        assert "ExecStartPre=/bin/mkdir" not in service


def test_kiosk_direct_boot_does_not_use_lightdm_in_kickstart():
    with tempfile.TemporaryDirectory() as tmpdir:
        builder = _make_builder(tmpdir, enable_lightdm=True, password="")
        builder._generate_kickstart("")
        with open(builder.ks_path, encoding="utf-8") as handle:
            kickstart = handle.read()
        assert "systemctl enable kiosk.service" in kickstart
        assert "systemctl set-default multi-user.target" in kickstart
        assert "systemctl enable lightdm.service" not in kickstart
        assert "lightdm-elephant-greeter" not in kickstart
        assert "usermod -L kioskuser" in kickstart
        assert "PAMName=login" not in kickstart
        assert "chage --lastday 0 kioskuser" not in kickstart
        assert "$6$" not in kickstart


def test_kiosk_direct_boot_with_sway_does_not_add_lightdm():
    with tempfile.TemporaryDirectory() as tmpdir:
        builder = _make_builder(
            tmpdir,
            enable_lightdm=True,
            multi_app=True,
            app2_mode="chromium",
            app2_url="http://example.com/segunda",
        )
        service = builder._sway_service_section(
            builder._resolve_app()["exec"],
            builder._resolve_app2()["exec"],
        )
        assert "systemctl enable kiosk.service" in service
        assert "systemctl enable lightdm.service" not in service
        pkgs = builder._package_lines(
            builder._resolve_app(), builder._resolve_app2()
        )
        assert "lightdm" not in pkgs


def test_kickstart_partition_sizing():
    with tempfile.TemporaryDirectory() as tmpdir:
        builder = _make_builder(tmpdir)
        builder._generate_kickstart(builder._password_hash())
        with open(builder.ks_path, encoding="utf-8") as handle:
            kickstart = handle.read()

        assert "zerombr" in kickstart
        assert "clearpart --all" in kickstart
        assert "part / --size 20480 --fstype ext4" in kickstart


def test_invalid_package_names_helper():
    assert invalid_package_names("") == []
    assert invalid_package_names(None) == []
    assert invalid_package_names("htop git tmux") == []
    assert invalid_package_names("htop,git,vim") == []
    assert invalid_package_names("foo;bar baz$(x)") == ["foo;bar", "baz$(x)"]
    assert invalid_package_names("pkg@1") == ["pkg@1"]
    assert invalid_package_names('"rm" -rf /') == ['"rm"', "-rf", "/"]


def test_extra_packages_rejected_when_invalid():
    builder = KioskISOBuilder(
        {
            "iso_name": "TestKiosk",
            "app_mode": "chromium",
            "extra_packages": "htop git; rm -rf /",
        }
    )
    with pytest.raises(RuntimeError, match="Paquetes adicionales"):
        builder._package_lines(builder._resolve_app())


def test_kickstart_file_is_private():
    with tempfile.TemporaryDirectory() as tmpdir:
        builder = _make_builder(tmpdir)
        builder._generate_kickstart(builder._password_hash())
        mode = os.stat(builder.ks_path).st_mode & 0o777
        assert mode == 0o600


def test_firefox_es_locale_policy():
    builder = KioskISOBuilder(
        {
            "iso_name": "TestKiosk",
            "app_mode": "firefox-es",
            "app_url": "http://example.com",
        }
    )
    app = builder._resolve_app()
    assert app["exec"].startswith("/usr/bin/firefox --kiosk")
    assert "firefox" in app["packages"]
    assert "firefox-langpacks" in app["packages"]
    assert "/etc/firefox/policies/policies.json" in app["post"]
    assert '"RequestedLocales": ["es-AR"]' in app["post"]

    with tempfile.TemporaryDirectory() as tmpdir:
        b = _make_builder(tmpdir, app_mode="firefox-es")
        b._generate_kickstart(b._password_hash())
        with open(b.ks_path, encoding="utf-8") as handle:
            kickstart = handle.read()
        assert "/etc/firefox/policies/policies.json" in kickstart
        assert "RequestedLocales" in kickstart


def test_firefox_es_as_second_app():
    builder = KioskISOBuilder(
        {
            "iso_name": "TestKiosk",
            "app_mode": "chromium",
            "multi_app": True,
            "app2_mode": "firefox-es",
            "app2_url": "http://example.com/segunda",
        }
    )
    app2 = builder._resolve_app2()
    assert app2["exec"].startswith("/usr/bin/firefox --kiosk")
    assert "firefox-langpacks" in app2["packages"]
    assert "RequestedLocales" in app2["post"]


def test_sway_wifi_shortcut_and_polkit(tmp_path):
    builder = _make_builder(
        str(tmp_path),
        multi_app=True,
        app2_mode="firefox-es",
        app2_url="http://example.com/segunda",
    )
    section = builder._sway_service_section(
        builder._resolve_app()["exec"], builder._resolve_app2()["exec"]
    )
    # Atajo Alt+9 / Super+9 y ventana flotante del editor de redes.
    assert "bindsym Mod1+9 exec /usr/local/bin/kiosk-wifi" in section
    assert "bindsym $mod+9 exec /usr/local/bin/kiosk-wifi" in section
    assert 'for_window [app_id="nm-connection-editor"] floating enable' in section
    # El script crea un bus de sesion temporal si hace falta.
    assert "dbus-run-session -- /usr/bin/nm-connection-editor" in section
    # Regla polkit para administrar la red sin agente interactivo.
    assert "/etc/polkit-1/rules.d/49-kiosk-network.rules" in section
    assert 'action.id.indexOf("org.freedesktop.NetworkManager.") == 0' in section
    # Paquetes del editor de conexiones.
    pkgs = builder._package_lines(builder._resolve_app(), builder._resolve_app2())
    for pkg in ("network-manager-applet", "polkit", "dbus-daemon"):
        assert pkg in pkgs


def test_cage_mode_has_no_wifi_editor(tmp_path):
    builder = _make_builder(str(tmp_path))
    section = builder._cage_service_section(builder._resolve_app()["exec"])
    assert "kiosk-wifi" not in section
    assert "49-kiosk-network.rules" not in section
    pkgs = builder._package_lines(builder._resolve_app())
    assert "network-manager-applet" not in pkgs
    assert "dbus-daemon" not in pkgs


def test_run_livecd_aborta_cuando_se_cancela(monkeypatch, tmp_path):
    builder = _make_builder(str(tmp_path))
    builder._priv = []
    builder.log_path = str(tmp_path / "livecd.log")
    builder.cancel_event = threading.Event()

    signals_sent = []

    class FakeStdout:
        def fileno(self):
            return 999

        def close(self):
            pass

    class FakeProcess:
        pid = 12345
        stdout = FakeStdout()

        def poll(self):
            return None

        def wait(self, timeout=None):
            return 0

        def send_signal(self, sig):
            signals_sent.append(sig)

    def fake_popen(*args, **kwargs):
        # El usuario cancela apenas arranca livecd-creator: el evento se
        # activa despues del chequeo inicial de _run_livecd.
        builder.cancel_event.set()
        return FakeProcess()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    monkeypatch.setattr(select, "select", lambda r, w, x, t=1.0: ([], [], []))
    monkeypatch.setattr(KioskISOBuilder, "_cleanup_stale_builds", lambda self: None)

    logs = []
    builder.log_signal.connect(logs.append)

    assert builder._run_livecd() is False
    joined = "\n".join(logs)
    assert "Cancelando livecd-creator" in joined
    assert "Compilacion cancelada por el usuario." in joined
    # El arbol de procesos recibio SIGTERM (killpg del pid inexistente cae
    # en el fallback send_signal).
    assert signal.SIGTERM in signals_sent


def test_product_name_branding(tmp_path):
    builder = _make_builder(
        str(tmp_path), product_name="TallerArgOS Fedora Kiosk"
    )
    section = builder._branding_section()
    # /etc/os-release: pantallas de Anaconda (WebUI) y hostnamectl.
    assert "base64 -d" in section
    assert "TallerArgOS Fedora Kiosk" not in section
    assert "rm -f /etc/os-release" in section
    assert (
        "sed -e '/^NAME=/d' -e '/^PRETTY_NAME=/d' /usr/lib/os-release" in section
    )
    # /etc/system-release: liveinst toma de ahi ANACONDA_PRODUCTNAME.
    assert "base64 -d > /etc/system-release" in section


def test_product_name_reaches_kickstart(tmp_path):
    builder = _make_builder(
        str(tmp_path), product_name="TallerArgOS Fedora Kiosk"
    )
    builder._generate_kickstart(builder._password_hash())
    with open(builder.ks_path, encoding="utf-8") as handle:
        kickstart = handle.read()
    assert "base64 -d" in kickstart
    assert "TallerArgOS Fedora Kiosk" not in kickstart
    assert "base64 -d > /etc/system-release" in kickstart

    # Sin nombre de producto la identidad de Fedora queda intacta.
    plain = _make_builder(str(tmp_path))
    plain._generate_kickstart(plain._password_hash())
    with open(plain.ks_path, encoding="utf-8") as handle:
        kickstart_plain = handle.read()
    assert "rm -f /etc/os-release" not in kickstart_plain
    assert "rm -f /etc/system-release" not in kickstart_plain


def test_product_name_invalid_characters(tmp_path):
    for bad in ('Kiosk"2026', "Kiosk\\2026", "Kiosk$2026", "Kiosk\n2026"):
        builder = _make_builder(str(tmp_path), product_name=bad)
        with pytest.raises(RuntimeError):
            builder._branding_section()


def test_product_name_empty_disables_branding(tmp_path):
    builder = _make_builder(str(tmp_path), product_name="   ")
    assert builder._branding_section() == ""



def test_ssh_is_disabled_by_default_and_opt_in():
    default = KioskISOBuilder({"iso_name": "TestKiosk", "password": "test-password"})
    assert default.enable_ssh is False
    assert "sshd.service" not in default._post_base("$6$hash")

    enabled = KioskISOBuilder({
        "iso_name": "TestKiosk", "password": "test-password",
        "enable_ssh": True, "ssh_password_auth": False,
    })
    post = enabled._post_base("$6$hash")
    assert "systemctl enable sshd.service" in post
    assert "PasswordAuthentication no" in post


def test_product_branding_uses_base64_for_shell_safe_injection():
    builder = KioskISOBuilder({
        "iso_name": "TestKiosk", "version": "1.0",
        "product_name": "TallerArgOS & Kiosk",
    })
    section = builder._branding_section()
    assert "base64 -d" in section
    assert "TallerArgOS & Kiosk" not in section


def test_product_branding_rejects_os_release_quote_and_newline():
    for value in ('Bad"Name', "Bad\\Name", "Bad\nName"):
        builder = KioskISOBuilder({"product_name": value})
        with pytest.raises(RuntimeError, match="nombre del producto"):
            builder._branding_section()


def test_check_disk_rejects_insufficient_space(tmp_path, monkeypatch):
    import shutil
    from collections import namedtuple

    builder = _make_builder(str(tmp_path))
    usage = namedtuple("Usage", "total used free")
    monkeypatch.setattr(shutil, "disk_usage", lambda path: usage(100, 90, 10))
    with pytest.raises(RuntimeError, match="Espacio insuficiente"):
        builder._check_disk()


def test_check_disk_rejects_tmpfs(tmp_path, monkeypatch):
    import shutil
    from collections import namedtuple

    builder = _make_builder(str(tmp_path))
    usage = namedtuple("Usage", "total used free")
    monkeypatch.setattr(shutil, "disk_usage", lambda path: usage(100, 10, 90))
    monkeypatch.setattr(
        "core.builder.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout="tmpfs\n", stderr=""
        ),
    )
    with pytest.raises(RuntimeError, match="tmpfs"):
        builder._check_disk()


# --- Regresiones de la ETAPA 2 (estabilizacion) ------------------------------


def test_multiventana_instala_nm_connection_editor(tmp_path):
    """Alt+9 ejecuta nm-connection-editor: el paquete debe estar presente."""
    builder = _make_builder(str(tmp_path), multi_app=True)
    packages = builder._package_lines(
        {"packages": ["chromium"]}, {"packages": ["firefox"]}
    )
    assert "nm-connection-editor" in packages


def test_installer_boot_preserves_efi_loader_commands():
    """La entrada UEFI debe conservar linuxefi/initrdefi del grub original."""
    builder = KioskISOBuilder({})
    section = builder._installer_boot_section()
    assert '$linux_line kiosk.mode=installer' in section
    assert '$initrd_line' in section
    # No debe reescribir la entrada como "linux ..." fijo (falla en UEFI).
    assert 'echo "    linux $linux' not in section
    assert 'echo "    initrd $initrd' not in section


def test_kickstart_post_uses_erroronfail_and_self_check(tmp_path):
    builder = _make_builder(str(tmp_path))
    builder._generate_kickstart("$6$fake$hash")
    with open(builder.ks_path, encoding="utf-8") as handle:
        kickstart = handle.read()
    assert "%post --erroronfail" in kickstart
    assert "Autoverificacion del %post" in kickstart
    assert "__kiosk_fail" in kickstart
    assert "kioskuser no tiene la contrasena bloqueada para el modo Live" in kickstart


def test_generated_post_scripts_are_valid_shell(tmp_path):
    """Los %post generados (incluida la autoverificacion) deben ser sh -n."""
    builder = _make_builder(
        str(tmp_path),
        multi_app=True,
        enable_installer=True,
        enable_lightdm=False,
        product_name="TallerArgOS Prueba",
    )
    builder._generate_kickstart("$6$fake$hash")
    with open(builder.ks_path, encoding="utf-8") as handle:
        kickstart = handle.read()

    posts = re.findall(r"%post(?:[^\n]*)\n(.*?)\n%end", kickstart, re.S)
    assert posts
    for index, body in enumerate(posts):
        script = tmp_path / f"post-{index}.sh"
        script.write_text(body, encoding="utf-8")
        result = subprocess.run(
            ["sh", "-n", str(script)], capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr


def test_final_check_covers_installer_greeter_and_apps(tmp_path):
    builder = _make_builder(
        str(tmp_path),
        multi_app=True,
        enable_installer=True,
        enable_lightdm=True,
    )
    section = builder._final_check_section(
        {"exec": "/usr/bin/chromium --kiosk http://example.com"},
        {"exec": "firefox --kiosk http://example.com"},
    )
    assert "/etc/systemd/system/kiosk.service" in section
    assert "/usr/bin/liveinst" in section
    assert "kioskuser no tiene la contrasena bloqueada" in section
    assert "/usr/local/bin/elephant-greeter.py" not in section
    assert "/usr/local/bin/kiosk-app-1.cmd" in section
    assert "/usr/local/bin/kiosk-app-2.cmd" in section
    assert "/usr/bin/chromium" in section
    assert "firefox" in section


def test_exec_binaries_ignores_urls_and_flags():
    binaries = KioskISOBuilder._exec_binaries(
        "/usr/bin/chromium --kiosk 'http://example.com/a?b=c'"
    )
    assert binaries == ["/usr/bin/chromium"]

    python_app = KioskISOBuilder._exec_binaries(
        "/usr/bin/python3 /opt/kiosk_app/main.py"
    )
    assert python_app == ["/usr/bin/python3", "/opt/kiosk_app/main.py"]

    custom = KioskISOBuilder._exec_binaries("htop -d 10")
    assert custom == ["htop"]


def test_validate_product_name_matches_backend_rules():
    assert validate_product_name("") is None
    assert validate_product_name("TallerArgOS Kiosco 2.0") is None
    assert "comillas" in validate_product_name('Nombre "raro"')
    assert "barras invertidas" in validate_product_name("Nombre\\raro")
    assert "$" in validate_product_name("Nombre $USER")
    assert "control" in validate_product_name("Nombre\nraro")
    assert "80" in validate_product_name("x" * 81)


def test_preflight_reports_all_missing_tools(monkeypatch):
    import shutil

    builder = KioskISOBuilder({})
    monkeypatch.setattr(shutil, "which", lambda name: None)
    monkeypatch.setattr(os.path, "isfile", lambda path: False)
    with pytest.raises(RuntimeError) as error:
        builder._preflight()
    message = str(error.value)
    assert "mkefiboot" in message
    assert "xorrisofs" in message
    assert "syslinux" in message
    assert "sudo dnf install" in message


def test_preflight_requires_createrepo_for_local_rpm(monkeypatch, tmp_path):
    import shutil

    rpm_path = tmp_path / "app.rpm"
    rpm_path.write_bytes(b"not-a-real-rpm")
    builder = KioskISOBuilder(
        {
            "app_mode": "custom",
            "app_path": str(rpm_path),
        }
    )

    def fake_which(name):
        if name in ("createrepo_c", "rpm"):
            return None
        return "/usr/bin/" + name

    monkeypatch.setattr(shutil, "which", fake_which)
    with pytest.raises(RuntimeError, match="createrepo_c"):
        builder._preflight()


def test_blocked_extra_packages_rejected():
    builder = KioskISOBuilder({"extra_packages": "firefox telnet"})
    with pytest.raises(RuntimeError, match="bloqueados"):
        builder._package_lines({"packages": []})


def test_boot_menu_splash_disabled_without_selected_image():
    builder = KioskISOBuilder({"app_mode": "chromium"})
    assert builder._boot_menu_splash_section() == ""


def test_boot_menu_splash_installs_bios_and_uefi_background_idempotently(tmp_path):
    import subprocess

    splash = tmp_path / "source.png"
    splash.write_bytes(b"fake-png-data")
    builder = KioskISOBuilder({
        "app_mode": "chromium",
        "plymouth_image": str(splash),
    })
    section = builder._boot_menu_splash_section()
    assert "%post --nochroot" in section
    assert "MENU BACKGROUND kiosk-splash.png" in section
    assert "UI vesamenu.c32" in section
    assert "background_image --mode=stretch" in section
    assert "if insmod gfxterm" in section

    install_root = tmp_path / "install"
    live_root = tmp_path / "live"
    theme_dir = install_root / "usr/share/plymouth/themes/kiosk"
    isolinux_dir = live_root / "isolinux"
    efi_dir = live_root / "EFI/BOOT"
    theme_dir.mkdir(parents=True)
    isolinux_dir.mkdir(parents=True)
    efi_dir.mkdir(parents=True)
    (theme_dir / "logo.png").write_bytes(splash.read_bytes())
    isolinux_cfg = isolinux_dir / "isolinux.cfg"
    isolinux_cfg.write_text(
        "label linux0\n  menu label Start Live\n"
        "  kernel vmlinuz0\n  append initrd=initrd0.img quiet\n",
        encoding="utf-8",
    )
    grub_cfg = efi_dir / "grub.cfg"
    grub_cfg.write_text(
        "menuentry 'Start Live' {\n linux /vmlinuz0 quiet\n"
        " initrd /initrd0.img\n}\n",
        encoding="utf-8",
    )

    script = section.replace("%post --nochroot", "", 1).replace("%end", "", 1)
    script_path = tmp_path / "boot-menu-splash.sh"
    script_path.write_text(script, encoding="utf-8")
    env = os.environ.copy()
    env.update({"LIVE_ROOT": str(live_root), "INSTALL_ROOT": str(install_root)})
    first = subprocess.run(["bash", str(script_path)], env=env, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    second = subprocess.run(["bash", str(script_path)], env=env, capture_output=True, text=True)
    assert second.returncode == 0, second.stderr

    assert (isolinux_dir / "kiosk-splash.png").read_bytes() == splash.read_bytes()
    assert (efi_dir / "kiosk-splash.png").read_bytes() == splash.read_bytes()
    bios = isolinux_cfg.read_text(encoding="utf-8")
    uefi = grub_cfg.read_text(encoding="utf-8")
    assert bios.count("MENU BACKGROUND kiosk-splash.png") == 1
    assert bios.count("UI vesamenu.c32") == 1
    assert uefi.count("background_image --mode=stretch") == 1
