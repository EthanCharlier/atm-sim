""" """

# ============================================================================
# IMPORT
# ============================================================================
from datetime import UTC, datetime
from pathlib import Path

# EXCEPTIONS IMPORT
from atm_sim.exceptions.exceptions import (
    AircraftDatabaseDownloadError,
    ConfigFileError,
    InvalidSimulationPeriodError,
    MultipleSelectionModesError,
)


# ============================================================================
# TESTS
# ============================================================================
def test_invalid_simulation_period_error_message() -> None:
    """ """
    begin = datetime(2026, 9, 1, 6, 0, tzinfo=UTC)
    end = datetime(2026, 9, 1, 5, 0, tzinfo=UTC)

    error = InvalidSimulationPeriodError(begin, end)

    assert isinstance(error, ValueError)
    assert str(begin) in str(error)
    assert str(end) in str(error)


def test_multiple_selection_modes_error_message() -> None:
    """ """
    error = MultipleSelectionModesError()

    assert isinstance(error, ValueError)
    assert "--airport" in str(error)


def test_aircraft_database_download_error_message() -> None:
    """ """
    url = "https://opensky-network.org/aircraft-database.csv"

    error = AircraftDatabaseDownloadError(url)

    assert isinstance(error, OSError)
    assert url in str(error)


def test_config_file_error_message() -> None:
    """ """
    path = Path("config.yaml")

    error = ConfigFileError(path, "unsupported extension")

    assert isinstance(error, ValueError)
    assert "config.yaml" in str(error)
    assert "unsupported extension" in str(error)
