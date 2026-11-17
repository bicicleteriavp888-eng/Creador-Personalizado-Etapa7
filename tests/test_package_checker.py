"""Pruebas unitarias para el comprobador de paquetes en repositorios."""

from core.repositories.package_checker import check_package_exists, invalid_package_names


def test_invalid_package_names():
    assert invalid_package_names("valid-pkg, another_pkg") == []
    assert len(invalid_package_names("bad;pkg, space pkg")) > 0


def test_check_package_exists():
    # Paquete común que suele existir o ser simulado
    assert check_package_exists("") is False
    assert check_package_exists("kernel") is True
