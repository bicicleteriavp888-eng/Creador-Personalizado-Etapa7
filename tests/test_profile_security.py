import pytest
from core.profiles.manager import save_profile, load_profile, delete_profile, export_profile, import_profile


def test_profile_crud_import_export(tmp_path):
    root = tmp_path / "profiles"
    save_profile("custom-one", {"profile_name": "Custom"}, root)
    assert load_profile("custom-one", root)["schema_version"] == 1
    exported = export_profile("custom-one", tmp_path / "export.json", root)
    import_profile(exported, "custom-two", root)
    assert load_profile("custom-two", root)["profile_name"] == "Custom"
    assert delete_profile("custom-two", root)


def test_profile_path_traversal_rejected(tmp_path):
    with pytest.raises(ValueError):
        save_profile("../../outside", {}, tmp_path)
