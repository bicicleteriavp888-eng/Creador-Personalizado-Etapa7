"""Tests del modulo core/usb.py: enumeracion de discos y progreso de dd."""

import json
import subprocess

import pytest

from core import usb


def _lsblk_result(stdout="", returncode=0, stderr=""):
    return subprocess.CompletedProcess(
        args=["lsblk"], returncode=returncode, stdout=stdout, stderr=stderr
    )


def _disk(name, **overrides):
    """Disco USB tipico tal como lo reporta lsblk -J -b."""
    device = {
        "name": name,
        "path": f"/dev/{name}",
        "type": "disk",
        "size": 32 * 1024 ** 3,
        "rm": True,
        "ro": False,
        "hotplug": False,
        "tran": "usb",
        "model": "USB Disk",
        "serial": "SN-1",
        "maj:min": "8:16",
        "mountpoints": [],
        "children": [],
    }
    device.update(overrides)
    return device


def _devices_json(*devices):
    return json.dumps({"blockdevices": list(devices)})


def _patch_lsblk(monkeypatch, stdout="", returncode=0, stderr=""):
    monkeypatch.setattr(usb.shutil, "which", lambda name: "/usr/bin/lsblk")
    monkeypatch.setattr(
        usb.subprocess,
        "run",
        lambda *args, **kwargs: _lsblk_result(stdout, returncode, stderr),
    )


# -- Utilidades ------------------------------------------------------------


def test_is_system_mount():
    # Raiz y subarboles del sistema.
    for mount in ("/", "/boot", "/boot/efi", "/var", "/var/tmp", "/home/x",
                  "/etc", "/opt/y", "/root", "/srv", "/usr"):
        assert usb._is_system_mount(mount) is True, mount

    # Puntos de montaje tipicos de medios extraibles.
    for mount in ("/media/usb", "/mnt", "/run/media/user/KINGSTON"):
        assert usb._is_system_mount(mount) is False, mount

    # Prefijo similar pero distinto no cuenta.
    assert usb._is_system_mount("/bootstrap") is False
    assert usb._is_system_mount("/homey") is False


def test_size_gib():
    assert usb.size_gib(1024 ** 3) == 1.0
    assert usb.size_gib(0) == 0.0
    assert usb.size_gib(None) == 0.0
    assert usb.size_gib("no-numero") == 0.0
    assert usb.size_gib("1073741824") == 1.0


def test_mountpoints_normalization():
    assert usb._mountpoints({"mountpoints": ["/a", ""]}) == ["/a"]
    assert usb._mountpoints({"mountpoints": "/b"}) == ["/b"]
    assert usb._mountpoints({"mountpoints": None}) == []
    assert usb._mountpoints({}) == []
    assert usb._mountpoints({"mountpoints": ["", None]}) == []


# -- list_usb_disks --------------------------------------------------------


def test_list_usb_disks_requires_lsblk(monkeypatch):
    monkeypatch.setattr(usb.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="lsblk"):
        usb.list_usb_disks()


def test_list_usb_disks_raises_on_lsblk_failure(monkeypatch):
    _patch_lsblk(monkeypatch, returncode=1, stderr="lsblk: error fatal")
    with pytest.raises(RuntimeError, match="lsblk fallo"):
        usb.list_usb_disks()


def test_list_usb_disks_raises_on_bad_json(monkeypatch):
    _patch_lsblk(monkeypatch, stdout="esto no es json")
    with pytest.raises(RuntimeError, match="interpretar la salida"):
        usb.list_usb_disks()


def test_list_usb_disks_keeps_only_removable_usb_disks(monkeypatch):
    devices = [
        _disk("sda", rm=False, hotplug=False, tran="sata", model="Disco SATA"),
        _disk("sdb"),
        _disk("sdc", ro=True),
        {"name": "sdb1", "type": "part", "path": "/dev/sdb1"},
    ]
    _patch_lsblk(monkeypatch, _devices_json(*devices))

    disks = usb.list_usb_disks()
    assert [disk["path"] for disk in disks] == ["/dev/sdb"]
    assert disks[0]["model"] == "USB Disk"
    assert disks[0]["serial"] == "SN-1"
    assert disks[0]["major_minor"] == "8:16"
    assert disks[0]["removable"] is True
    assert disks[0]["tran"] == "usb"
    assert disks[0]["size"] == 32 * 1024 ** 3


def test_list_usb_disks_excludes_system_disks(monkeypatch):
    devices = [
        # Host arrancado desde USB: raiz en el propio dispositivo.
        _disk("sdd", mountpoints=["/"]),
        # Disco del sistema con /boot/efi en una particion hija.
        _disk(
            "sde",
            children=[
                {
                    "name": "sde1",
                    "path": "/dev/sde1",
                    "mountpoints": ["/boot/efi"],
                }
            ],
        ),
        _disk("sdb"),
    ]
    _patch_lsblk(monkeypatch, _devices_json(*devices))

    disks = usb.list_usb_disks()
    assert [disk["path"] for disk in disks] == ["/dev/sdb"]


def test_list_usb_disks_keeps_data_disks_with_media_mounts(monkeypatch):
    # Un USB con datos montados en /run/media SI se ofrece: es el caso de
    # uso normal (se avisa al usuario antes de borrar).
    usb_disk = _disk(
        "sdb",
        children=[
            {
                "name": "sdb1",
                "path": "/dev/sdb1",
                "mountpoints": ["/run/media/user/KINGSTON"],
            }
        ],
    )
    _patch_lsblk(monkeypatch, _devices_json(usb_disk))

    disks = usb.list_usb_disks()
    assert [disk["path"] for disk in disks] == ["/dev/sdb"]


def test_list_usb_disks_merges_child_mountpoints(monkeypatch):
    usb_disk = _disk(
        "sdb",
        children=[
            {
                "name": "sdb1",
                "path": "/dev/sdb1",
                "mountpoints": ["/run/media/user/KINGSTON"],
            },
            {"name": "sdb2", "path": "/dev/sdb2", "mountpoints": None},
        ],
    )
    _patch_lsblk(monkeypatch, _devices_json(usb_disk))

    disks = usb.list_usb_disks()
    assert len(disks) == 1
    assert "/run/media/user/KINGSTON" in disks[0]["mountpoints"]
    assert [child["path"] for child in disks[0]["children"]] == [
        "/dev/sdb1",
        "/dev/sdb2",
    ]
    assert disks[0]["children"][0]["mountpoints"] == [
        "/run/media/user/KINGSTON"
    ]


def test_list_usb_disks_accepts_usb_without_removable_flag(monkeypatch):
    # Algunos pendrives reportan rm=0; si TRAN dice usb se acepta igual.
    _patch_lsblk(monkeypatch, _devices_json(_disk("sdb", rm=False, hotplug=False)))
    disks = usb.list_usb_disks()
    assert len(disks) == 1
    assert disks[0]["removable"] is False


def test_list_usb_disks_accepts_hotplug_without_usb_transport(monkeypatch):
    # Discos NVMe externos: sin TRAN pero marcados hotplug.
    _patch_lsblk(monkeypatch, _devices_json(_disk("sdb", hotplug=True, tran="")))
    disks = usb.list_usb_disks()
    assert len(disks) == 1
    assert disks[0]["removable"] is True


def test_list_usb_disks_path_fallback_to_dev_name(monkeypatch):
    device = _disk("sdb")
    device.pop("path")
    _patch_lsblk(monkeypatch, _devices_json(device))
    disks = usb.list_usb_disks()
    assert disks[0]["path"] == "/dev/sdb"


def test_list_usb_disks_skips_non_dev_paths(monkeypatch):
    _patch_lsblk(monkeypatch, _devices_json(_disk("sdb", path="/mapper/loop0")))
    assert usb.list_usb_disks() == []


# -- USBWriterWorker._handle_output ----------------------------------------


def test_handle_output_progress_and_log_gate():
    worker = usb.USBWriterWorker("/tmp/fake.iso", "/dev/null")
    logs = []
    progress = []
    worker.log_signal.connect(logs.append)
    worker.progress_signal.connect(progress.append)

    iso_size = 10 * 1024 * 1024

    # Primer reporte de dd: "N bytes copied".
    last = worker._handle_output("1048576 bytes copied", iso_size, -10)
    assert progress == [10]
    assert last == 10
    assert len(logs) == 1

    last = worker._handle_output("2097152 bytes copied", iso_size, last)
    assert progress == [10, 20]
    assert last == 20
    assert len(logs) == 2

    # Menos de 5 puntos mas: mueve la barra pero no escribe log.
    # (2359296 bytes = 2.25 MiB = 22% de la ISO de 10 MiB.)
    last = worker._handle_output("2359296 bytes copied", iso_size, last)
    assert progress == [10, 20, 22]
    assert last == 20
    assert len(logs) == 2

    # El progreso queda en 99% hasta el final (el 100 lo emite run()).
    last = worker._handle_output("999999999999 bytes copied", iso_size, last)
    assert progress[-1] == 99
    assert last == 99

    # Lineas normales van al log y no tocan el progreso.
    frozen_progress = list(progress)
    last = worker._handle_output("ERROR: /dev/sdb1 sigue montado", iso_size, last)
    assert logs[-1] == "ERROR: /dev/sdb1 sigue montado"
    assert progress == frozen_progress
    assert last == 99

    # Lineas vacias no hacen nada.
    assert worker._handle_output("   ", iso_size, last) == last
    assert worker._handle_output("", iso_size, last) == last
    assert progress == frozen_progress


def test_validate_device_snapshot_accepts_same_device():
    current = {"major_minor": "8:16", "size": 32, "serial": "SN-1", "model": "USB"}
    usb._validate_device_snapshot(current, dict(current))


def test_validate_device_snapshot_rejects_replaced_device():
    current = {"major_minor": "8:32", "size": 32, "serial": "SN-2", "model": "USB"}
    original = {"major_minor": "8:16", "size": 32, "serial": "SN-1", "model": "USB"}
    with pytest.raises(RuntimeError, match="major_minor"):
        usb._validate_device_snapshot(current, original)


def test_validate_device_snapshot_requires_kernel_identity():
    with pytest.raises(RuntimeError, match="MAJ:MIN"):
        usb._validate_device_snapshot({"size": 32}, {"size": 32})


# -- USBWriterWorker._build_write_script ----------------------------------------


def _writer_with_snapshot(snapshot):
    return usb.USBWriterWorker("/tmp/fake.iso", "/dev/sdb", device_snapshot=snapshot)


def test_build_write_script_trims_lsblk_output():
    worker = _writer_with_snapshot(
        {
            "major_minor": "8:16",
            "size": 32 * 1024 ** 3,
            "serial": "SN-1",
            "model": "USB",
        }
    )
    script = worker._build_write_script(
        "/tmp/fake.iso",
        "/dev/sdb",
        worker.device_snapshot,
        [],
        [],
        32 * 1024 ** 3,
    )
    assert any(
        "actual_mm=$(lsblk -dn -o MAJ:MIN -- /dev/sdb | tr -d '[:space:]')" in line
        for line in script
    )
    assert any(
        "ERROR: identidad MAJ:MIN cambiada" in line for line in script
    )


def test_build_write_script_identity_mismatch_exits_20():
    worker = _writer_with_snapshot(
        {"major_minor": "8:32", "size": 32 * 1024 ** 3}
    )
    script = worker._build_write_script(
        "/tmp/fake.iso",
        "/dev/sdb",
        worker.device_snapshot,
        [],
        [],
        32 * 1024 ** 3,
    )
    joined = "\n".join(script)
    assert "ERROR: identidad MAJ:MIN cambiada" in joined
    assert "exit 20" in joined


def test_build_write_script_serial_mismatch_exits_22():
    worker = _writer_with_snapshot(
        {"major_minor": "8:16", "size": 32 * 1024 ** 3, "serial": "SN-2"}
    )
    script = worker._build_write_script(
        "/tmp/fake.iso",
        "/dev/sdb",
        worker.device_snapshot,
        [],
        [],
        32 * 1024 ** 3,
    )
    joined = "\n".join(script)
    assert "ERROR: numero de serie cambiado" in joined
    assert "exit 22" in joined


def test_build_write_script_mounted_exits_with_constant():
    worker = _writer_with_snapshot({"major_minor": "8:16", "size": 32 * 1024 ** 3})
    script = worker._build_write_script(
        "/tmp/fake.iso",
        "/dev/sdb",
        worker.device_snapshot,
        ["/dev/sdb1"],
        [],
        32 * 1024 ** 3,
    )
    joined = "\n".join(script)
    assert "ERROR: /dev/sdb1 sigue montado" in joined
    assert "exit 3" in joined


def test_build_write_script_ok_includes_dd_and_cmp():
    worker = _writer_with_snapshot({"major_minor": "8:16", "size": 32 * 1024 ** 3})
    script = worker._build_write_script(
        "/tmp/fake.iso",
        "/dev/sdb",
        worker.device_snapshot,
        [],
        [],
        32 * 1024 ** 3,
    )
    joined = "\n".join(script)
    assert "dd if=" in joined
    assert "of=/dev/sdb" in joined
    assert "cmp -n" in joined
