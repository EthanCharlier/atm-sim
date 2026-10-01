""" """

# ============================================================================
# IMPORT
# ============================================================================
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path


# ============================================================================
# CLASS
# ============================================================================
class InvalidSimulationPeriodError(ValueError):
    """ """

    def __init__(
        self,
        begin: datetime,
        end: datetime,
    ) -> None:
        """ """
        super().__init__(f"start ({begin}) must be before end ({end})")


class MultipleSelectionModesError(ValueError):
    """ """

    def __init__(self) -> None:
        """ """
        super().__init__("Only one selection mode allowed: --airport, --origin/--destination, --callsign, or --icao24")


class AircraftDatabaseDownloadError(OSError):
    """ """

    def __init__(
        self,
        url: str,
    ) -> None:
        """ """
        super().__init__(f"Failed to download aircraft database from {url}")


class ConfigFileError(ValueError):
    """ """

    def __init__(
        self,
        path: Path,
        reason: str,
    ) -> None:
        """ """
        super().__init__(f"Invalid config file {path}: {reason}")


class InsufficientTrajectoryPointsError(ValueError):
    """ """

    def __init__(
        self,
        minimum_points: int,
    ) -> None:
        """ """
        super().__init__(f"TrajectoryEntity requires at least {minimum_points} points")
