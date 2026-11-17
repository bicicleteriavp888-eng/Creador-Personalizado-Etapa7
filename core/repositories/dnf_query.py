"""Consultas y simulaciones seguras DNF para seleccionar software.

Este módulo consulta repositorios, busca paquetes, lista grupos comps y puede
simular una transacción con ``--assumeno``. No confirma ni aplica operaciones
en el anfitrión. Está pensado para Fedora 44 (DNF5), con respaldo textual para
la consulta de repositorios en versiones anteriores.

Reglas de seguridad:

* todos los comandos se ejecutan con una lista de argumentos y ``shell=False``;
* la búsqueda del usuario se valida y se pasa después de ``--``;
* los identificadores de grupo se validan antes de usarse;
* se aplica un tiempo de espera y se acota el tamaño de los mensajes de error;
* la salida se interpreta como datos, nunca se evalúa como shell.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass

from core.software.policy import (
    GROUP_ID_PATTERN,
    SoftwareSelectionError,
    normalize_group_entry,
    normalize_search_query,
    validate_package_names,
)

DEFAULT_TIMEOUT = 180
DEFAULT_RESULT_LIMIT = 500
MAX_RESULT_LIMIT = 2000
MAX_ERROR_CHARS = 800

# DNF interpreta las secuencias \t y \n de este formato. Se usa una tabulación
# real en el argumento para que la salida sea inequívoca también en DNF5.
PACKAGE_QUERY_FORMAT = (
    "%{name}\t%{summary}\t%{reponame}\t%{version}\t%{arch}\n"
)

_ARCH_SUFFIXES = frozenset(
    {
        "aarch64",
        "armv7hl",
        "i386",
        "i486",
        "i586",
        "i686",
        "noarch",
        "nosrc",
        "ppc64le",
        "s390x",
        "src",
        "x86_64",
    }
)
_GROUP_SECTIONS = {
    "Mandatory packages": "mandatory",
    "Default packages": "default",
    "Optional packages": "optional",
    "Conditional packages": "conditional",
}
_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class DnfRepository:
    """Repositorio DNF habilitado."""

    id: str
    name: str
    enabled: bool = True


@dataclass(frozen=True)
class DnfPackage:
    """Resultado de búsqueda de un paquete."""

    name: str
    summary: str = ""
    repository: str = ""
    version: str = ""
    architecture: str = ""


@dataclass(frozen=True)
class DnfGroup:
    """Grupo comps disponible."""

    id: str
    name: str
    installed: bool = False


@dataclass(frozen=True)
class DnfGroupDetails:
    """Detalle de un grupo comps, incluyendo sus listas de paquetes."""

    id: str
    name: str
    description: str = ""
    installed: bool = False
    repositories: tuple[str, ...] = ()
    mandatory: tuple[str, ...] = ()
    default: tuple[str, ...] = ()
    optional: tuple[str, ...] = ()
    conditional: tuple[str, ...] = ()


class DnfQueryError(RuntimeError):
    """DNF no está disponible o la consulta no pudo completarse."""


class DnfUnavailableError(DnfQueryError):
    """El ejecutable de DNF no está instalado."""


def _clean_text(value, limit=None):
    text = _ANSI_ESCAPE_RE.sub("", str(value or ""))
    text = _CONTROL_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    if limit is not None:
        text = text[:limit]
    return text


def _strip_arch(spec):
    """Quita el sufijo de arquitectura de una salida de ``dnf search``."""
    name, dot, arch = spec.rpartition(".")
    if dot and arch in _ARCH_SUFFIXES:
        return name
    return spec


def _normalize_limit(limit):
    try:
        value = int(limit)
    except (TypeError, ValueError) as exc:
        raise ValueError("El límite de resultados debe ser un número entero.") from exc
    if value < 1:
        raise ValueError("El límite de resultados debe ser mayor que cero.")
    return min(value, MAX_RESULT_LIMIT)


def _add_package_names(target, raw):
    for value in re.split(r"[\s,]+", str(raw or "")):
        if not value:
            continue
        result = validate_package_names([value])
        if result["allowed"]:
            target.append(result["allowed"][0])


def _add_group_section_packages(target, raw, section):
    value = str(raw or "")
    if section == "conditional":
        # DNF puede expresar condiciones como "paquete if otro-paquete".
        value = re.split(r"\s+if\s+", value, maxsplit=1)[0]
    _add_package_names(target, value)


class DnfQuery:
    """Adaptador de consultas DNF inyectable para pruebas."""

    def __init__(
        self,
        dnf_binary=None,
        timeout=DEFAULT_TIMEOUT,
        runner=None,
        which=None,
        env=None,
    ):
        try:
            timeout = int(timeout)
        except (TypeError, ValueError) as exc:
            raise ValueError("El tiempo de espera de DNF debe ser numérico.") from exc
        if timeout < 1:
            raise ValueError("El tiempo de espera de DNF debe ser mayor que cero.")
        self.dnf_binary = dnf_binary
        self.timeout = timeout
        self._runner = runner or subprocess.run
        self._which = which or shutil.which
        self._env = dict(env or {})

    def available(self):
        """Indica si hay un ejecutable de DNF configurado o en ``PATH``."""
        return bool(self.dnf_binary or self._which("dnf5") or self._which("dnf"))

    def _binary(self):
        binary = self.dnf_binary or self._which("dnf5") or self._which("dnf")
        if not binary:
            raise DnfUnavailableError(
                "No se encontró dnf. Instalá DNF en el equipo Fedora."
            )
        return binary

    def _environment(self):
        env = os.environ.copy()
        # Locale estable para que los encabezados y las columnas de DNF no
        # dependan del idioma del usuario.
        env["LC_ALL"] = "C.UTF-8"
        env["LANG"] = "C.UTF-8"
        env["LANGUAGE"] = ""
        env.update(self._env)
        return env

    def _run(self, args):
        command = [self._binary(), "-q", *args]
        try:
            proc = self._runner(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                check=False,
                stdin=subprocess.DEVNULL,
                env=self._environment(),
            )
        except FileNotFoundError as exc:
            raise DnfUnavailableError(
                "No se encontró dnf. Instalá DNF en el equipo Fedora."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise DnfQueryError(
                f"La consulta DNF superó {self.timeout} segundos."
            ) from exc
        except OSError as exc:
            raise DnfQueryError(
                "No se pudo ejecutar DNF: " + _clean_text(str(exc), MAX_ERROR_CHARS)
            ) from exc

        if proc.returncode:
            detail = _clean_text(
                proc.stderr or proc.stdout or "", MAX_ERROR_CHARS
            )
            if not detail:
                detail = f"DNF terminó con código {proc.returncode}."
            raise DnfQueryError("DNF no pudo completar la consulta: " + detail)
        return proc.stdout or ""

    # -- Repositorios --------------------------------------------------------

    def list_enabled_repositories(self):
        """Lista los repositorios habilitados, ordenados por identificador."""
        try:
            output = self._run(["repolist", "--enabled", "--json"])
        except DnfUnavailableError:
            raise
        except DnfQueryError:
            output = self._run(["repolist", "--enabled"])
            return self._parse_repositories_text(output)

        try:
            return self._parse_repositories_json(output)
        except (ValueError, TypeError, json.JSONDecodeError):
            text_output = self._run(["repolist", "--enabled"])
            return self._parse_repositories_text(text_output)

    def _parse_repositories_json(self, output):
        data = json.loads(output)
        if not isinstance(data, list):
            raise ValueError("La salida JSON de repolist no es una lista.")
        repositories, seen = [], set()
        for item in data:
            if not isinstance(item, dict):
                continue
            repo_id = _clean_text(item.get("id"), 200)
            name = _clean_text(item.get("name"), 300)
            enabled = bool(item.get("is_enabled", True))
            if not enabled or not repo_id or not name or repo_id in seen:
                continue
            if any(ch.isspace() for ch in repo_id):
                continue
            seen.add(repo_id)
            repositories.append(DnfRepository(repo_id, name, True))
        repositories.sort(key=lambda repo: repo.id.casefold())
        return repositories

    def _parse_repositories_text(self, output):
        repositories, seen = [], set()
        for raw in output.splitlines():
            line = _ANSI_ESCAPE_RE.sub("", raw).strip()
            if not line or line.lower().startswith("repo id"):
                continue
            parts = re.split(r"\s{2,}", line, maxsplit=2)
            if len(parts) < 2:
                continue
            repo_id, name = _clean_text(parts[0], 200), _clean_text(parts[1], 300)
            if not repo_id or not name or repo_id in seen:
                continue
            if any(ch.isspace() for ch in repo_id):
                continue
            seen.add(repo_id)
            repositories.append(DnfRepository(repo_id, name, True))
        repositories.sort(key=lambda repo: repo.id.casefold())
        return repositories

    # -- Paquetes ------------------------------------------------------------

    def search_packages(self, query="", limit=DEFAULT_RESULT_LIMIT):
        """Busca paquetes por nombre o descripción.

        Con una consulta usa ``dnf search --all``; con la consulta vacía
        consulta el catálogo completo con ``repoquery``. La búsqueda se pasa
        después de ``--`` para que DNF nunca la interprete como una opción.
        """
        query = normalize_search_query(query)
        limit = _normalize_limit(limit)
        if query:
            # DNF5 no tiene --search en repoquery. ``dnf search`` recibe cada
            # término como patrón separado; se pasan después de ``--`` para que
            # ninguno pueda interpretarse como una opción.
            output = self._run(["search", "--all", "--", *query.split()])
            return self._parse_search_output(output, limit)
        output = self._run(
            [
                "repoquery",
                "--available",
                "--latest-limit=1",
                "--qf",
                PACKAGE_QUERY_FORMAT,
            ]
        )
        return self._parse_repoquery_output(output, limit)

    def _parse_search_output(self, output, limit):
        packages, seen = [], set()
        for raw in output.splitlines():
            line = _ANSI_ESCAPE_RE.sub("", raw).strip()
            if "\t" not in line or line.startswith("Matched fields:"):
                continue
            spec, summary = line.split("\t", 1)
            name = _clean_text(_strip_arch(spec.strip()), 200)
            if not name or name in seen:
                continue
            if not validate_package_names([name])["allowed"]:
                continue
            seen.add(name)
            packages.append(DnfPackage(name=name, summary=_clean_text(summary, 500)))
            if len(packages) >= limit:
                break
        return packages

    def _parse_repoquery_output(self, output, limit):
        packages, seen = [], set()
        for raw in output.splitlines():
            parts = raw.split("\t", 4)
            if len(parts) < 2:
                continue
            name = _clean_text(parts[0], 200)
            if not name or name in seen:
                continue
            if not validate_package_names([name])["allowed"]:
                continue
            seen.add(name)
            packages.append(
                DnfPackage(
                    name=name,
                    summary=_clean_text(parts[1], 500),
                    repository=_clean_text(parts[2], 300) if len(parts) > 2 else "",
                    version=_clean_text(parts[3], 100) if len(parts) > 3 else "",
                    architecture=(
                        _clean_text(parts[4], 40) if len(parts) > 4 else ""
                    ),
                )
            )
            if len(packages) >= limit:
                break
        return packages

    # -- Resolución transaccional (simulación segura) -----------------------

    def preview_installation(self, packages=(), groups=()):
        """Resuelve paquetes y grupos con DNF5 sin aplicar la transacción.

        ``--assumeno`` hace que DNF5 rechace la confirmación final: el solver
        calcula dependencias/conflictos usando los repositorios habilitados,
        pero no instala, elimina ni actualiza paquetes del anfitrión.
        Se devuelve la salida completa para conservar el detalle exacto de DNF.
        """
        package_result = validate_package_names(list(packages))
        if package_result["invalid"] or package_result["blocked"]:
            raise SoftwareSelectionError(
                "La selección contiene paquetes inválidos o bloqueados."
            )
        normalized_groups = []
        for group in groups:
            normalized_groups.append(normalize_group_entry(group))
        specs = sorted(set(package_result["allowed"])) + sorted(set(normalized_groups))
        if not specs:
            raise SoftwareSelectionError(
                "Seleccioná al menos un paquete o grupo antes de resolver dependencias."
            )
        # No se usa --skip-broken ni --allowerasing: un conflicto debe quedar
        # visible y nunca ocultarse quitando software automáticamente.
        return self._run(["--assumeno", "install", *specs])

    # -- Grupos comps --------------------------------------------------------

    def list_groups(self):
        """Lista los grupos comps disponibles, incluidos los ocultos."""
        return self._parse_groups(self._run(["group", "list", "--hidden"]))

    def _parse_groups(self, output):
        groups, seen = [], set()
        for raw in output.splitlines():
            line = _ANSI_ESCAPE_RE.sub("", raw).rstrip()
            match = re.match(r"^(\S+)\s{2,}(.*?)\s{2,}(yes|no)$", line)
            if not match:
                continue
            group_id = match.group(1).strip()
            name = _clean_text(match.group(2), 300)
            if not GROUP_ID_PATTERN.fullmatch(group_id) or not name:
                continue
            if group_id in seen:
                continue
            seen.add(group_id)
            groups.append(
                DnfGroup(group_id, name, match.group(3).strip() == "yes")
            )
        groups.sort(key=lambda group: (group.name.casefold(), group.id.casefold()))
        return groups

    def group_info(self, group_id):
        """Devuelve el detalle de un grupo comps o ``None`` si no existe.

        Acepta ``office``, ``@office`` o ``@^office`` y consulta siempre con el
        identificador sin prefijo.
        """
        entry = normalize_group_entry(group_id)
        identifier = entry[2:] if entry.startswith("@^") else entry[1:]
        return self._parse_group_info(self._run(["group", "info", identifier]))

    def _parse_group_info(self, output):
        fields = {}
        package_lists = {
            "mandatory": [],
            "default": [],
            "optional": [],
            "conditional": [],
        }
        current_section = None

        for raw in output.splitlines():
            line = _ANSI_ESCAPE_RE.sub("", raw).rstrip()
            if not line.strip():
                continue
            key, separator, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if key:
                current_section = _GROUP_SECTIONS.get(key)
                if current_section:
                    if value:
                        _add_group_section_packages(
                            package_lists[current_section], value, current_section
                        )
                    continue
                if separator:
                    fields[key] = value
                current_section = None
            elif current_section and value:
                _add_group_section_packages(
                    package_lists[current_section], value, current_section
                )

        identifier = _clean_text(fields.get("Id"), 64)
        if not identifier:
            return None
        name = _clean_text(fields.get("Name"), 300) or identifier
        repositories = tuple(
            repo
            for repo in (
                _clean_text(value, 200)
                for value in re.split(r"[\s,]+", fields.get("Repositories", ""))
            )
            if repo
        )
        return DnfGroupDetails(
            id=identifier,
            name=name,
            description=_clean_text(fields.get("Description"), 1000),
            installed=str(fields.get("Installed", "")).strip().lower()
            in ("yes", "true", "1"),
            repositories=repositories,
            mandatory=tuple(package_lists["mandatory"]),
            default=tuple(package_lists["default"]),
            optional=tuple(package_lists["optional"]),
            conditional=tuple(package_lists["conditional"]),
        )


__all__ = [
    "DEFAULT_RESULT_LIMIT",
    "DnfGroup",
    "DnfGroupDetails",
    "DnfPackage",
    "DnfQuery",
    "DnfQueryError",
    "DnfRepository",
    "DnfUnavailableError",
    "MAX_RESULT_LIMIT",
    "PACKAGE_QUERY_FORMAT",
    "SoftwareSelectionError",
]
