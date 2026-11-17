"""Gestion de repositorios Fedora usados por el Kickstart."""

import urllib.request

from core.constants import DEFAULT_MIRRORLIST, FEDORA_ARCH, FEDORA_RELEASE

USER_AGENT = "Creador-kiosk/2.0"


class RepositoryManager:
    """Construye y verifica las directivas ``repo`` del Kickstart.

    Acepta un mirror fijo con layout Fedora (``releases/`` + ``updates/``) o
    el mirrorlist oficial, que permite failover automatico durante el build.
    La verificacion es solo informativa: dnf reintenta por su cuenta.
    """

    def __init__(
        self,
        mirror="",
        mirrorlist=DEFAULT_MIRRORLIST,
        release=FEDORA_RELEASE,
        arch=FEDORA_ARCH,
        emit=None,
    ):
        self.mirror = (mirror or "").rstrip("/")
        self.mirrorlist = (mirrorlist or DEFAULT_MIRRORLIST).rstrip("/")
        self.release = str(release or FEDORA_RELEASE)
        self.arch = arch
        self.emit = emit

    def _log(self, message):
        if self.emit is not None:
            self.emit(message)

    def lines(self):
        """Lineas ``repo`` del Kickstart (mirrorlist oficial o mirror fijo)."""
        if self.mirror:
            return (
                f"repo --name=fedora --baseurl={self.mirror}/releases/"
                f"{self.release}/Everything/{self.arch}/os/\n"
                f"repo --name=updates --baseurl={self.mirror}/updates/"
                f"{self.release}/Everything/{self.arch}/"
            )
        return (
            f"repo --name=fedora --mirrorlist={self.mirrorlist}"
            f"?repo=fedora-{self.release}&arch={self.arch}\n"
            f"repo --name=updates --mirrorlist={self.mirrorlist}"
            f"?repo=updates-released-f{self.release}&arch={self.arch}"
        )

    def _mirror_metadata_url(self):
        return (
            f"{self.mirror}/releases/{self.release}/Everything/"
            f"{self.arch}/os/repodata/repomd.xml"
        )

    def _mirrorlist_url(self):
        return (
            f"{self.mirrorlist}?repo=fedora-{self.release}&arch={self.arch}"
        )

    def check(self):
        """Comprueba el repositorio configurado sin abortar el build."""
        if self.mirror:
            self._check_fixed_mirror()
        else:
            self._check_mirrorlist()

    def _check_fixed_mirror(self):
        url = self._mirror_metadata_url()
        self._log(f"🌐 Repos: mirror fijo {self.mirror}")
        try:
            request = urllib.request.Request(
                url, method="HEAD", headers={"User-Agent": USER_AGENT}
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status != 200:
                    self._log(
                        f"⚠ El repositorio respondio HTTP {response.status}: {url}"
                    )
        except Exception as exc:  # noqa: BLE001 - solo es un aviso
            self._log(
                f"⚠ No pude verificar el repositorio ({exc}). "
                f"Si el build falla con 404, revisa KIOSK_MIRROR={self.mirror}"
            )

    def _check_mirrorlist(self):
        url = self._mirrorlist_url()
        self._log("🌐 Repos: mirrorlist oficial de Fedora (failover automatico)")
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": USER_AGENT}
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                mirrors = [
                    line.strip()
                    for line in response.read().decode("utf-8", "replace").splitlines()
                    if line.strip().startswith(("http://", "https://"))
                ]
            if not mirrors:
                self._log("⚠ El mirrorlist no devolvio mirrors utilizables.")
        except Exception as exc:  # noqa: BLE001 - solo es un aviso
            self._log(
                f"⚠ No pude consultar el mirrorlist ({exc}). dnf lo "
                "reintentara durante la compilacion."
            )
