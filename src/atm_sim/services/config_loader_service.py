""" """

# ============================================================================
# IMPORT
# ============================================================================
import tomllib
from typing import TYPE_CHECKING, Any

import yaml

# EXCEPTIONS IMPORT
from atm_sim.exceptions.exceptions import ConfigFileError

if TYPE_CHECKING:
    from pathlib import Path


# ============================================================================
# CLASS
# ============================================================================
class ConfigLoaderService:
    """ """

    @staticmethod
    def load(
        path: Path,
    ) -> dict[str, Any]:
        """ """
        suffix = path.suffix.lower()

        try:
            if suffix == ".toml":
                with path.open("rb") as file:
                    return tomllib.load(file)

            if suffix in (".yaml", ".yml"):
                with path.open(encoding="utf-8") as file:
                    return yaml.safe_load(file) or {}
        except (OSError, tomllib.TOMLDecodeError, yaml.YAMLError) as error:
            raise ConfigFileError(path, str(error)) from error

        raise ConfigFileError(path, f"unsupported format {suffix!r} (expected .toml, .yaml or .yml)")
