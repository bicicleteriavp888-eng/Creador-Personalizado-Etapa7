"""Pruebas del adaptador de consultas DNF, sin red ni DNF real."""

import json
import subprocess

import pytest

from core.repositories.dnf_query import (
    DnfQuery,
    DnfQueryError,
    DnfUnavailableError,
)
from core.software.policy import SoftwareSelectionError


class FakeResult:
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


class Recorder:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def __call__(self, command, **kwargs):
        self.calls.append((command, kwargs))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def _query(outcomes):
    recorder = Recorder(outcomes)
    query = DnfQuery(
        dnf_binary="/usr/bin/dnf",
        runner=recorder,
        which=lambda _name: None,
    )
    return query, recorder


def test_available_repositories_json_is_parsed_and_sorted():
    payload = [
        {"id": "updates", "name": "Fedora Updates", "is_enabled": True},
        {"id": "fedora", "name": "Fedora 44", "is_enabled": True},
        {"id": "disabled", "name": "No usar", "is_enabled": False},
    ]
    query, recorder = _query([FakeResult(stdout=json.dumps(payload))])
    repositories = query.list_enabled_repositories()

    assert [repo.id for repo in repositories] == ["fedora", "updates"]
    assert repositories[0].name == "Fedora 44"
    command, kwargs = recorder.calls[0]
    assert command == ["/usr/bin/dnf", "-q", "repolist", "--enabled", "--json"]
    assert kwargs.get("shell", False) is False
    assert kwargs["stdin"] == subprocess.DEVNULL
    assert "LC_ALL" in kwargs["env"]
    assert kwargs["env"]["LC_ALL"] == "C.UTF-8"


def test_repository_text_output_is_used_when_json_is_not_supported():
    text = (
        "repo id                   repo name                     status\n"
        "fedora                    Fedora 44 - x86_64            70000\n"
        "updates                   Fedora 44 - x86_64 - Updates  1200\n"
    )
    query, recorder = _query(
        [
            FakeResult(stderr="opción --json desconocida", returncode=2),
            FakeResult(stdout=text),
        ]
    )
    repositories = query.list_enabled_repositories()

    assert [repo.id for repo in repositories] == ["fedora", "updates"]
    assert [repo.name for repo in repositories] == [
        "Fedora 44 - x86_64",
        "Fedora 44 - x86_64 - Updates",
    ]
    assert len(recorder.calls) == 2


def test_invalid_repository_json_falls_back_to_text():
    text = "fedora    Fedora 44\n"
    query, recorder = _query(
        [FakeResult(stdout="{no es json"), FakeResult(stdout=text)]
    )
    repositories = query.list_enabled_repositories()

    assert [repo.id for repo in repositories] == ["fedora"]
    assert len(recorder.calls) == 2


def test_package_search_uses_separated_query_and_parses_results():
    output = (
        "Matched fields: name (exact)\n"
        " htop.x86_64\tInteractive process viewer\n"
        " pcp-htop.x86_64\tPerformance Co-Pilot interactive process viewer\n"
        " htop.x86_64\tDuplicado\n"
        " bad;name.x86_64\tEntrada inválida\n"
    )
    query, recorder = _query([FakeResult(stdout=output)])
    packages = query.search_packages("htop", limit=10)

    assert [(pkg.name, pkg.summary) for pkg in packages] == [
        ("htop", "Interactive process viewer"),
        ("pcp-htop", "Performance Co-Pilot interactive process viewer"),
    ]
    command, kwargs = recorder.calls[0]
    assert command == [
        "/usr/bin/dnf",
        "-q",
        "search",
        "--all",
        "--",
        "htop",
    ]
    assert kwargs.get("shell", False) is False


def test_full_catalog_uses_repoquery_and_parses_repository_details():
    output = (
        "git\tFast Version Control System\tFedora 44 - x86_64\t2.56.1\n"
        "htop\tInteractive process viewer\tFedora 44 - x86_64\t3.4.1\n"
        "git\tVersión duplicada\tOtro repo\t2.0.0\n"
    )
    query, recorder = _query([FakeResult(stdout=output)])
    packages = query.search_packages("", limit=1)

    assert len(packages) == 1
    assert packages[0].name == "git"
    assert packages[0].repository == "Fedora 44 - x86_64"
    assert packages[0].version == "2.56.1"
    command, _kwargs = recorder.calls[0]
    assert command[2] == "repoquery"
    assert "--latest-limit=1" in command


def test_repoquery_parses_architecture_when_dnf_provides_it():
    output = "gimp\tImage editor\tfedora\t2.10.38\tx86_64\n"
    query, recorder = _query([FakeResult(stdout=output)])
    packages = query.search_packages("", limit=1)

    assert packages[0].architecture == "x86_64"
    command, _kwargs = recorder.calls[0]
    query_format = command[command.index("--qf") + 1]
    assert "%{arch}" in query_format


def test_search_query_is_validated_before_running_dnf():
    query, recorder = _query([])
    for value in ("-peligro", "linea\nnueva", "x" * 121):
        with pytest.raises(SoftwareSelectionError):
            query.search_packages(value)
    assert recorder.calls == []


def test_result_limit_is_validated():
    query, recorder = _query([])
    with pytest.raises(ValueError):
        query.search_packages("htop", limit=0)
    with pytest.raises(ValueError):
        query.search_packages("htop", limit="muchos")
    assert recorder.calls == []


def test_groups_are_parsed_sorted_and_deduplicated():
    output = (
        "ID                          Name                                        Installed\n"
        "office                      Office/Productivity                         no\n"
        "multimedia                  Multimedia                                  yes\n"
        "office                      Duplicado                                   no\n"
        "bad id                      Inválido                                    no\n"
    )
    query, recorder = _query([FakeResult(stdout=output)])
    groups = query.list_groups()

    assert [(group.id, group.name, group.installed) for group in groups] == [
        ("multimedia", "Multimedia", True),
        ("office", "Office/Productivity", False),
    ]
    assert recorder.calls[0][0] == [
        "/usr/bin/dnf",
        "-q",
        "group",
        "list",
        "--hidden",
    ]


def test_group_info_is_parsed_with_all_package_sections():
    output = (
        "Id                   : office\n"
        "Name                 : Office/Productivity\n"
        "Description          : Suite de oficina\n"
        "Installed            : no\n"
        "Repositories         : fedora, updates\n"
        "Mandatory packages   : libreoffice-core\n"
        "Default packages     : libreoffice-writer\n"
        "                     : libreoffice-calc\n"
        "Optional packages    : abiword\n"
        "Conditional packages : paquete-cond if otro-paquete\n"
    )
    query, recorder = _query([FakeResult(stdout=output)])
    details = query.group_info("@office")

    assert details is not None
    assert details.id == "office"
    assert details.name == "Office/Productivity"
    assert details.repositories == ("fedora", "updates")
    assert details.mandatory == ("libreoffice-core",)
    assert details.default == ("libreoffice-writer", "libreoffice-calc")
    assert details.optional == ("abiword",)
    assert details.conditional == ("paquete-cond",)
    assert recorder.calls[0][0] == [
        "/usr/bin/dnf",
        "-q",
        "group",
        "info",
        "office",
    ]


def test_group_info_returns_none_when_group_does_not_exist():
    query, _recorder = _query([FakeResult(stdout="")])
    assert query.group_info("no-existe") is None


def test_invalid_group_id_is_rejected_before_running_dnf():
    query, recorder = _query([])
    with pytest.raises(SoftwareSelectionError):
        query.group_info("@grupo con espacios")
    assert recorder.calls == []


def test_missing_dnf_raises_unavailable_error():
    query = DnfQuery(which=lambda _name: None)
    assert query.available() is False
    with pytest.raises(DnfUnavailableError, match="dnf"):
        query.list_groups()


def test_dnf5_binary_is_detected_before_legacy_dnf():
    calls = []
    def which(name):
        calls.append(name)
        return "/usr/bin/dnf5" if name == "dnf5" else None
    query = DnfQuery(which=which)
    assert query.available() is True
    assert calls == ["dnf5"]


def test_dnf_failure_is_sanitized_and_truncated():
    query, _recorder = _query(
        [
            FakeResult(
                stderr="\x1b[31mError\x1b[0m\n" + "detalle " * 500,
                returncode=1,
            )
        ]
    )
    with pytest.raises(DnfQueryError) as error:
        query.list_groups()
    message = str(error.value)
    assert "\x1b" not in message
    assert "\n" not in message
    assert len(message) < 1000


def test_timeout_is_reported_as_query_error():
    query, _recorder = _query(
        [subprocess.TimeoutExpired(cmd=["dnf"], timeout=1)]
    )
    with pytest.raises(DnfQueryError, match="180 segundos"):
        query.list_groups()


def test_constructor_rejects_invalid_timeout():
    with pytest.raises(ValueError):
        DnfQuery(timeout=0)
    with pytest.raises(ValueError):
        DnfQuery(timeout="mucho")


def test_multi_term_search_passes_each_term_after_separator():
    query, recorder = _query([FakeResult(stdout="")])
    query.search_packages("servidor web")
    command, _kwargs = recorder.calls[0]
    assert command == [
        "/usr/bin/dnf",
        "-q",
        "search",
        "--all",
        "--",
        "servidor",
        "web",
    ]


def test_preview_installation_uses_assumeno_and_includes_packages_and_groups():
    query, recorder = _query(
        [FakeResult(stdout="Transaction Summary:\n Installing: 3 packages\n")]
    )
    output = query.preview_installation(["htop", "git"], ["@office"])

    assert "Transaction Summary" in output
    command, kwargs = recorder.calls[0]
    assert command == [
        "/usr/bin/dnf", "-q", "--assumeno", "install", "git", "htop", "@office"
    ]
    assert kwargs.get("shell", False) is False
    assert kwargs["stdin"] == subprocess.DEVNULL


def test_preview_installation_rejects_invalid_selection_before_running_dnf():
    query, recorder = _query([])
    with pytest.raises(SoftwareSelectionError):
        query.preview_installation(["--allowerasing"], [])
    with pytest.raises(SoftwareSelectionError):
        query.preview_installation([], [])
    assert recorder.calls == []


def test_preview_installation_propagates_solver_conflicts():
    query, recorder = _query(
        [FakeResult(stderr="Problem: package conflict", returncode=1)]
    )
    with pytest.raises(DnfQueryError, match="package conflict"):
        query.preview_installation(["htop"], [])
    assert len(recorder.calls) == 1
