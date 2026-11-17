from core.projects.catalog import get_project_template, list_project_types, merge_packages


def test_expected_project_archetypes_exist():
    keys = {key for key, _name, _tagline in list_project_types()}
    assert {"kiosk", "office", "web", "gaming", "security_lab", "custom"} <= keys


def test_templates_are_isolated_and_have_package_lists():
    first = get_project_template("office")
    first["packages"].append("injected-package")
    second = get_project_template("office")
    assert "injected-package" not in second["packages"]
    assert second["engine"] == "desktop"


def test_package_merge_deduplicates_and_validates():
    assert merge_packages(["firefox", "git"], "git, curl") == ["firefox", "git", "curl"]
    try:
        merge_packages(["valid", "bad;name"])
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid package name was accepted")
