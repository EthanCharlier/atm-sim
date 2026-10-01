""" """

# ============================================================================
# IMPORT
# ============================================================================
import urllib.error
import urllib.request
from pathlib import Path

import pytest

# EXCEPTIONS IMPORT
from atm_sim.exceptions.exceptions import AircraftDatabaseDownloadError

# SERVICES IMPORT
from atm_sim.services import aircraft_database_service as service_module
from atm_sim.services.aircraft_database_service import AircraftDatabaseService


# ============================================================================
# CONSTANTS
# ============================================================================
_CSV_HEADER = "icao24,registration,manufacturername,model,typecode,operator,extracolumn\n"


# ============================================================================
# HELPERS
# ============================================================================
def _write_cache(cache_path: Path, rows: str) -> None:
    """ """
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(_CSV_HEADER + rows, encoding="utf-8")


# ============================================================================
# TESTS — _ensure_cached
# ============================================================================
def test_init_skips_download_when_already_cached(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    cache_path = tmp_path / "aircraftDatabase.csv"
    _write_cache(cache_path, "abc123,F-GKXA,AIRBUS,A320,A320,AIR FRANCE,x\n")
    # noinspection PyUnresolvedReferences
    monkeypatch.setattr(service_module, "AIRCRAFT_DATABASE_CACHE_PATH", cache_path)

    def _fail_if_called(*_args: object, **_kwargs: object) -> None:
        pytest.fail("urlretrieve should not be called when the cache already exists")

    monkeypatch.setattr(urllib.request, "urlretrieve", _fail_if_called)

    AircraftDatabaseService()


def test_init_downloads_when_not_cached(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    cache_path = tmp_path / "nested" / "aircraftDatabase.csv"
    # noinspection PyUnresolvedReferences
    monkeypatch.setattr(service_module, "AIRCRAFT_DATABASE_CACHE_PATH", cache_path)

    calls: list[tuple[object, ...]] = []

    def _fake_urlretrieve(url: str, filename: str) -> None:
        calls.append((url, filename))
        _write_cache(cache_path, "abc123,F-GKXA,AIRBUS,A320,A320,AIR FRANCE,x\n")

    monkeypatch.setattr(urllib.request, "urlretrieve", _fake_urlretrieve)

    AircraftDatabaseService()

    assert len(calls) == 1


def test_init_wraps_download_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    cache_path = tmp_path / "aircraftDatabase.csv"
    # noinspection PyUnresolvedReferences
    monkeypatch.setattr(service_module, "AIRCRAFT_DATABASE_CACHE_PATH", cache_path)

    def _fake_urlretrieve(*_args: object, **_kwargs: object) -> None:
        raise urllib.error.URLError("network unreachable")

    monkeypatch.setattr(urllib.request, "urlretrieve", _fake_urlretrieve)

    with pytest.raises(AircraftDatabaseDownloadError):
        AircraftDatabaseService()


# ============================================================================
# TESTS — get_aircraft
# ============================================================================
def test_get_aircraft_returns_metadata_for_known_icao24(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ """
    cache_path = tmp_path / "aircraftDatabase.csv"
    _write_cache(cache_path, "3944ef,F-GKXA,AIRBUS,A320,A320,AIR FRANCE,x\n")
    # noinspection PyUnresolvedReferences
    monkeypatch.setattr(service_module, "AIRCRAFT_DATABASE_CACHE_PATH", cache_path)
    service = AircraftDatabaseService()

    metadata = service.get_aircraft("3944ef")

    assert metadata is not None
    assert metadata.registration == "F-GKXA"
    assert metadata.manufacturer == "AIRBUS"
    assert metadata.typecode == "A320"


def test_get_aircraft_is_case_insensitive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    cache_path = tmp_path / "aircraftDatabase.csv"
    _write_cache(cache_path, "3944ef,F-GKXA,AIRBUS,A320,A320,AIR FRANCE,x\n")
    # noinspection PyUnresolvedReferences
    monkeypatch.setattr(service_module, "AIRCRAFT_DATABASE_CACHE_PATH", cache_path)
    service = AircraftDatabaseService()

    assert service.get_aircraft("3944EF") is not None


def test_get_aircraft_returns_none_for_unknown_icao24(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    cache_path = tmp_path / "aircraftDatabase.csv"
    _write_cache(cache_path, "3944ef,F-GKXA,AIRBUS,A320,A320,AIR FRANCE,x\n")
    # noinspection PyUnresolvedReferences
    monkeypatch.setattr(service_module, "AIRCRAFT_DATABASE_CACHE_PATH", cache_path)
    service = AircraftDatabaseService()

    assert service.get_aircraft("ffffff") is None


def test_get_aircraft_blank_fields_become_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    cache_path = tmp_path / "aircraftDatabase.csv"
    _write_cache(cache_path, "3944ef,,,,,x\n")
    # noinspection PyUnresolvedReferences
    monkeypatch.setattr(service_module, "AIRCRAFT_DATABASE_CACHE_PATH", cache_path)
    service = AircraftDatabaseService()

    metadata = service.get_aircraft("3944ef")

    assert metadata is not None
    assert metadata.registration is None
    assert metadata.manufacturer is None


def test_duplicate_icao24_keeps_first_row(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    cache_path = tmp_path / "aircraftDatabase.csv"
    rows = (
        "3944ef,F-GKXA,AIRBUS,A320,A320,AIR FRANCE,x\n"
        "3944ef,F-DUPLICATE,BOEING,B738,B738,OTHER,x\n"
    )
    _write_cache(cache_path, rows)
    # noinspection PyUnresolvedReferences
    monkeypatch.setattr(service_module, "AIRCRAFT_DATABASE_CACHE_PATH", cache_path)
    service = AircraftDatabaseService()

    metadata = service.get_aircraft("3944ef")

    assert metadata is not None
    assert metadata.registration == "F-GKXA"
