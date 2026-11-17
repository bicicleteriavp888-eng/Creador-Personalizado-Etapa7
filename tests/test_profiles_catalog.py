"""Pruebas unitarias para perfiles y catálogo de aplicaciones (Etapa 5)."""

import os
import pytest

from core.profiles.manager import list_available_profiles, load_profile, save_profile, delete_profile
from core.catalog.catalog import load_catalog, get_applications_by_category, find_application


def test_profiles_listing():
    profiles = list_available_profiles()
    assert "kiosco-navegador" in profiles
    assert "kiosco-multiventana" in profiles
    assert "oficina" in profiles


def test_profile_load_and_save():
    profile = load_profile("kiosco-navegador")
    assert profile is not None
    assert profile["profile_name"] == "Kiosco Navegador"

    # Save as temp profile, then delete
    test_key = "test-profile-temp"
    save_profile(test_key, profile)
    loaded = load_profile(test_key)
    assert loaded["profile_name"] == "Kiosco Navegador"

    deleted = delete_profile(test_key)
    assert deleted is True
    assert load_profile(test_key) is None


def test_catalog_loading():
    cat = load_catalog()
    assert "categories" in cat
    assert "applications" in cat
    assert len(cat["applications"]) > 0


def test_catalog_search_and_category():
    app = find_application("chromium")
    assert app is not None
    assert app["name"] == "Chromium"

    nav_apps = get_applications_by_category("Navegadores")
    assert len(nav_apps) >= 2
