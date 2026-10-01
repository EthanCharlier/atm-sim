""" """

# ============================================================================
# IMPORT
# ============================================================================
from pathlib import Path

import pytest

# EXCEPTIONS IMPORT
from atm_sim.exceptions.exceptions import ConfigFileError

# SERVICES IMPORT
from atm_sim.services.config_loader_service import ConfigLoaderService


# ============================================================================
# TESTS — TOML
# ============================================================================
def test_load_valid_toml(tmp_path: Path) -> None:
    """ """
    config_path = tmp_path / "config.toml"
    config_path.write_text('airport = "LFBO"\nmax_flights = 5\n', encoding="utf-8")

    data = ConfigLoaderService.load(config_path)

    assert data == {"airport": "LFBO", "max_flights": 5}


def test_load_invalid_toml_raises_config_file_error(tmp_path: Path) -> None:
    """ """
    config_path = tmp_path / "config.toml"
    config_path.write_text("not = valid = toml", encoding="utf-8")

    with pytest.raises(ConfigFileError):
        ConfigLoaderService.load(config_path)


# ============================================================================
# TESTS — YAML
# ============================================================================
@pytest.mark.parametrize("extension", [".yaml", ".yml"])
def test_load_valid_yaml(tmp_path: Path, extension: str) -> None:
    """ """
    config_path = tmp_path / f"config{extension}"
    config_path.write_text("airport: [LFPG, LFBO]\nmax_flights: 15\n", encoding="utf-8")

    data = ConfigLoaderService.load(config_path)

    assert data == {"airport": ["LFPG", "LFBO"], "max_flights": 15}


def test_load_empty_yaml_returns_empty_dict(tmp_path: Path) -> None:
    """ """
    config_path = tmp_path / "config.yaml"
    config_path.write_text("", encoding="utf-8")

    assert ConfigLoaderService.load(config_path) == {}


def test_load_invalid_yaml_raises_config_file_error(tmp_path: Path) -> None:
    """ """
    config_path = tmp_path / "config.yaml"
    config_path.write_text("airport: [unclosed\n", encoding="utf-8")

    with pytest.raises(ConfigFileError):
        ConfigLoaderService.load(config_path)


# ============================================================================
# TESTS — error cases
# ============================================================================
def test_load_unsupported_extension_raises_config_file_error(tmp_path: Path) -> None:
    """ """
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")

    with pytest.raises(ConfigFileError, match="unsupported format"):
        ConfigLoaderService.load(config_path)


def test_load_missing_file_raises_config_file_error(tmp_path: Path) -> None:
    """ """
    config_path = tmp_path / "missing.toml"

    with pytest.raises(ConfigFileError):
        ConfigLoaderService.load(config_path)
