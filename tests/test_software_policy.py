"""Pruebas de las políticas compartidas de selección de software."""

import pytest

from core.software.policy import (
    GROUP_NAME_MAX,
    PACKAGE_NAME_MAX,
    SEARCH_QUERY_MAX,
    SoftwareSelectionError,
    normalize_group_entry,
    normalize_group_id,
    normalize_groups,
    normalize_package_entry,
    normalize_packages,
    normalize_search_query,
    validate_group_names,
    validate_package_names,
)


def test_package_policy_accepts_rpm_names_and_rejects_groups():
    result = validate_package_names("htop git gimp, @office")
    assert result == {
        "allowed": ["htop", "git", "gimp"],
        "blocked": [],
        "invalid": ["@office"],
    }


def test_package_policy_rejects_blocked_and_control_characters():
    result = validate_package_names(["telnet", "htop;rm", "paquete\nraro"])
    assert result["allowed"] == []
    assert result["blocked"] == ["telnet"]
    assert result["invalid"] == ["htop;rm", "paquete\nraro"]


def test_package_name_length_limit():
    name = "a" * PACKAGE_NAME_MAX
    assert normalize_package_entry(name) == name
    with pytest.raises(SoftwareSelectionError, match="supera"):
        normalize_package_entry(name + "a")


def test_normalize_packages_deduplicates_and_reports_all_problems():
    assert normalize_packages("htop git htop") == ["htop", "git"]
    with pytest.raises(SoftwareSelectionError) as error:
        normalize_packages("telnet htop;rm")
    message = str(error.value)
    assert "telnet" in message
    assert "htop;rm" in message
    assert "inválidos" in message


def test_group_policy_accepts_group_and_environment_entries():
    valid = validate_group_names(
        ["@office", "@^workstation-product-environment", "office"]
    )
    assert valid["allowed"] == [
        "@office",
        "@^workstation-product-environment",
    ]
    assert valid["invalid"] == ["office"]


def test_normalize_group_entry_variants():
    assert normalize_group_entry("office") == "@office"
    assert normalize_group_entry("@office") == "@office"
    assert normalize_group_entry("@^office") == "@^office"


def test_group_id_and_length_validation():
    assert normalize_group_id("office") == "office"
    with pytest.raises(SoftwareSelectionError):
        normalize_group_id("@office")
    with pytest.raises(SoftwareSelectionError):
        normalize_group_id("office grupo")
    with pytest.raises(SoftwareSelectionError):
        normalize_group_id("a" * (GROUP_NAME_MAX + 1))


def test_normalize_groups_deduplicates_and_rejects_invalid_entries():
    assert normalize_groups("office @office @^workstation") == [
        "@office",
        "@^workstation",
    ]
    with pytest.raises(SoftwareSelectionError, match="grupo"):
        normalize_groups(["@office", "@grupo con espacios"])


def test_search_query_accepts_unicode_and_rejects_unsafe_text():
    assert normalize_search_query("  editor de imágenes  ") == "editor de imágenes"
    assert normalize_search_query("") == ""
    for query in (
        "-peligro",
        "foo -bar",
        "linea\nnueva",
        "nul\x00",
        "x" * (SEARCH_QUERY_MAX + 1),
    ):
        with pytest.raises(SoftwareSelectionError):
            normalize_search_query(query)
