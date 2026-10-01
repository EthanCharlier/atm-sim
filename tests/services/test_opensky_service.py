""" """

# ============================================================================
# IMPORT
# ============================================================================
from datetime import UTC, datetime

import pandas as pd
import pytest
from trino.exceptions import Error as TrinoError

# ENTITIES IMPORT
from atm_sim.entities.aircraft_entity import AircraftEntity
from atm_sim.entities.aircraft_metadata_entity import AircraftMetadataEntity
from atm_sim.entities.airport_entity import AirportEntity
from atm_sim.entities.flight_query_spec_entity import FlightQuerySpecEntity
from atm_sim.entities.trajectory_entity import TrajectoryEntity
from atm_sim.entities.trajectory_point_entity import TrajectoryPointEntity
from atm_sim.services.opensky_service import (
    OpenSkyService,
    _build_query_specs,
    _distribute_quotas,
    _to_unix_seconds,
)


# ============================================================================
# HELPERS / FAKES
# ============================================================================
class _FakeTrino:
    """ """

    def __init__(
        self,
        flightlist_df: pd.DataFrame | None = None,
        flightlist_error: Exception | None = None,
        history_df: pd.DataFrame | None = None,
        history_error: Exception | None = None,
    ) -> None:
        """ """
        self._flightlist_df = flightlist_df
        self._flightlist_error = flightlist_error
        self._history_df = history_df
        self._history_error = history_error
        self.flightlist_calls: list[tuple[object, ...]] = []
        self.history_calls: list[tuple[object, ...]] = []

    def flightlist(self, begin: object, end: object, **kwargs: object) -> pd.DataFrame | None:
        """ """
        self.flightlist_calls.append((begin, end, kwargs))
        if self._flightlist_error is not None:
            raise self._flightlist_error
        return self._flightlist_df

    def history(self, begin: object, end: object, **kwargs: object) -> pd.DataFrame | None:
        """ """
        self.history_calls.append((begin, end, kwargs))
        if self._history_error is not None:
            raise self._history_error
        return self._history_df


class _FakeAirportService:
    """ """

    def __init__(self, airports: dict[str, AirportEntity] | None = None) -> None:
        """ """
        self._airports = airports or {}

    def get_airport(self, icao: str) -> AirportEntity | None:
        """ """
        return self._airports.get(icao.upper())


class _FakeAircraftDatabaseService:
    """ """

    def __init__(self, metadata_by_icao24: dict[str, AircraftMetadataEntity] | None = None) -> None:
        """ """
        self._metadata_by_icao24 = metadata_by_icao24 or {}

    def get_aircraft(self, icao24: str) -> AircraftMetadataEntity | None:
        """ """
        return self._metadata_by_icao24.get(icao24.lower())


def _make_aircraft(
    callsign: str = "AFR123",
    max_altitude_ft: float = 10000.0,
    max_ground_speed_kmh: float = 500.0,
    duration_seconds: float = 1000.0,
) -> AircraftEntity:
    """ """
    points = [
        TrajectoryPointEntity(
            time_offset_seconds=0.0,
            lat=0.0,
            lon=0.0,
            altitude_ft=0.0,
            ground_speed_kmh=0.0,
            vertical_rate_ft_per_min=0.0,
            on_ground=True,
        ),
        TrajectoryPointEntity(
            time_offset_seconds=duration_seconds,
            lat=1.0,
            lon=1.0,
            altitude_ft=max_altitude_ft,
            ground_speed_kmh=max_ground_speed_kmh,
            vertical_rate_ft_per_min=0.0,
            on_ground=False,
        ),
    ]
    return AircraftEntity(
        callsign=callsign,
        origin_airport=AirportEntity.unknown(),
        destination_airport=AirportEntity.unknown(),
        trajectory=TrajectoryEntity(points=points),
    )


def _make_service(
    trino: _FakeTrino | None = None,
    airport_service: _FakeAirportService | None = None,
    aircraft_database_service: _FakeAircraftDatabaseService | None = None,
) -> OpenSkyService:
    """ """
    return OpenSkyService(
        trino=trino or _FakeTrino(),  # type: ignore[arg-type]
        airport_service=airport_service or _FakeAirportService(),  # type: ignore[arg-type]
        aircraft_database_service=aircraft_database_service or _FakeAircraftDatabaseService(),  # type: ignore[arg-type]
    )


# ============================================================================
# TESTS — _to_unix_seconds
# ============================================================================
def test_to_unix_seconds_with_float_passthrough() -> None:
    """ """
    assert _to_unix_seconds(123.0) == pytest.approx(123.0)


def test_to_unix_seconds_with_timestamp() -> None:
    """ """
    timestamp = pd.Timestamp("2026-09-01T06:00:00", tz="UTC")

    assert _to_unix_seconds(timestamp) == pytest.approx(timestamp.timestamp())


# ============================================================================
# TESTS — _distribute_quotas
# ============================================================================
def test_distribute_quotas_evenly() -> None:
    """ """
    quotas = _distribute_quotas(num_specs=3, max_flights=9)

    assert quotas == [3, 3, 3]


def test_distribute_quotas_with_remainder() -> None:
    """ """
    quotas = _distribute_quotas(num_specs=3, max_flights=10)

    assert sum(quotas) == 10
    assert sorted(quotas) == [3, 3, 4]


# ============================================================================
# TESTS — _build_query_specs
# ============================================================================
def test_build_query_specs_airports_takes_priority() -> None:
    """ """
    specs = _build_query_specs(
        airports=["LFBO"], origins=["LFPG"], destinations=["LFPO"], callsigns=["AFR123"], icao24s=["abc"],
    )

    assert [s.airport for s in specs] == ["LFBO"]


def test_build_query_specs_origin_destination_cross_product() -> None:
    """ """
    specs = _build_query_specs(
        airports=None, origins=["LFBO", "LFPG"], destinations=["LFPO"], callsigns=None, icao24s=None,
    )

    assert [(s.departure_airport, s.arrival_airport) for s in specs] == [("LFBO", "LFPO"), ("LFPG", "LFPO")]


def test_build_query_specs_origins_only() -> None:
    """ """
    specs = _build_query_specs(airports=None, origins=["LFBO"], destinations=None, callsigns=None, icao24s=None)

    assert [s.departure_airport for s in specs] == ["LFBO"]


def test_build_query_specs_destinations_only() -> None:
    """ """
    specs = _build_query_specs(airports=None, origins=None, destinations=["LFPO"], callsigns=None, icao24s=None)

    assert [s.arrival_airport for s in specs] == ["LFPO"]


def test_build_query_specs_callsigns_only() -> None:
    """ """
    specs = _build_query_specs(airports=None, origins=None, destinations=None, callsigns=["AFR123"], icao24s=None)

    assert [s.callsign for s in specs] == ["AFR123"]


def test_build_query_specs_icao24s_only() -> None:
    """ """
    specs = _build_query_specs(airports=None, origins=None, destinations=None, callsigns=None, icao24s=["3944ef"])

    assert [s.icao24 for s in specs] == ["3944ef"]


def test_build_query_specs_nothing_returns_empty_list() -> None:
    """ """
    assert _build_query_specs(None, None, None, None, None) == []


# ============================================================================
# TESTS — _apply_post_filters
# ============================================================================
def test_apply_post_filters_min_altitude() -> None:
    """ """
    aircraft = _make_aircraft(max_altitude_ft=5000.0)

    filtered = OpenSkyService._apply_post_filters(  # noqa: SLF001
        [aircraft], min_altitude_ft=10000.0, max_altitude_ft=None,
        min_ground_speed_kmh=None, min_duration_seconds=None, airlines=None,
    )

    assert filtered == []


def test_apply_post_filters_max_altitude() -> None:
    """ """
    aircraft = _make_aircraft(max_altitude_ft=20000.0)

    filtered = OpenSkyService._apply_post_filters(  # noqa: SLF001
        [aircraft], min_altitude_ft=None, max_altitude_ft=15000.0,
        min_ground_speed_kmh=None, min_duration_seconds=None, airlines=None,
    )

    assert filtered == []


def test_apply_post_filters_min_speed() -> None:
    """ """
    aircraft = _make_aircraft(max_ground_speed_kmh=100.0)

    filtered = OpenSkyService._apply_post_filters(  # noqa: SLF001
        [aircraft], min_altitude_ft=None, max_altitude_ft=None,
        min_ground_speed_kmh=300.0, min_duration_seconds=None, airlines=None,
    )

    assert filtered == []


def test_apply_post_filters_min_duration() -> None:
    """ """
    aircraft = _make_aircraft(duration_seconds=100.0)

    filtered = OpenSkyService._apply_post_filters(  # noqa: SLF001
        [aircraft], min_altitude_ft=None, max_altitude_ft=None,
        min_ground_speed_kmh=None, min_duration_seconds=500.0, airlines=None,
    )

    assert filtered == []


def test_apply_post_filters_airline_prefix() -> None:
    """ """
    afr = _make_aircraft(callsign="AFR123")
    ryr = _make_aircraft(callsign="RYR456")

    filtered = OpenSkyService._apply_post_filters(  # noqa: SLF001
        [afr, ryr], min_altitude_ft=None, max_altitude_ft=None,
        min_ground_speed_kmh=None, min_duration_seconds=None, airlines=["afr"],
    )

    assert filtered == [afr]


def test_apply_post_filters_keeps_matching_aircraft() -> None:
    """ """
    aircraft = _make_aircraft()

    filtered = OpenSkyService._apply_post_filters(  # noqa: SLF001
        [aircraft], min_altitude_ft=None, max_altitude_ft=None,
        min_ground_speed_kmh=None, min_duration_seconds=None, airlines=None,
    )

    assert filtered == [aircraft]


# ============================================================================
# TESTS — _filter_valid_flights
# ============================================================================
def test_filter_valid_flights_keeps_only_complete_rows() -> None:
    """ """
    flights_df = pd.DataFrame(
        {
            "icao24": ["3944ef", None, "abcdef", "123456"],
            "firstseen": [1.0, 2.0, float("nan"), 4.0],
            "lastseen": [10.0, 20.0, 30.0, 40.0],
            "departure": ["LFBO", "LFPG", "LFPO", None],
            "arrival": ["LFPG", "LFBO", "LFPO", "LFPO"],
        },
    )

    valid = OpenSkyService._filter_valid_flights(flights_df)  # noqa: SLF001

    assert valid["icao24"].tolist() == ["3944ef"]


# ============================================================================
# TESTS — _resolve_airport
# ============================================================================
def test_resolve_airport_returns_unknown_for_non_string_code() -> None:
    """ """
    service = _make_service()

    airport = service._resolve_airport(None)  # noqa: SLF001

    assert airport.icao == "????"


def test_resolve_airport_returns_unknown_when_not_found() -> None:
    """ """
    service = _make_service(airport_service=_FakeAirportService({}))

    airport = service._resolve_airport("ZZZZ")  # noqa: SLF001

    assert airport.icao == "????"


def test_resolve_airport_returns_known_airport() -> None:
    """ """
    known = AirportEntity.unknown()
    known.icao = "LFBO"
    service = _make_service(airport_service=_FakeAirportService({"LFBO": known}))

    airport = service._resolve_airport("lfbo")  # noqa: SLF001

    assert airport.icao == "LFBO"


# ============================================================================
# TESTS — _select_flights_for_query
# ============================================================================
def _valid_flightlist_df() -> pd.DataFrame:
    """ """
    return pd.DataFrame(
        {
            "icao24": ["3944ef"],
            "firstseen": [1000.0],
            "lastseen": [2000.0],
            "departure": ["LFBO"],
            "arrival": ["LFPG"],
            "callsign": ["AFR123"],
        },
    )


def test_select_flights_for_query_returns_selected_rows() -> None:
    """ """
    trino = _FakeTrino(flightlist_df=_valid_flightlist_df())
    service = _make_service(trino=trino)
    begin = datetime(2026, 9, 1, 6, 0, tzinfo=UTC)
    end = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)

    result = service._select_flights_for_query(  # noqa: SLF001
        FlightQuerySpecEntity(airport="LFBO"), begin, end, quota=5,
    )

    assert result is not None
    assert result["icao24"].tolist() == ["3944ef"]


def test_select_flights_for_query_returns_none_on_empty_result() -> None:
    """ """
    trino = _FakeTrino(flightlist_df=pd.DataFrame())
    service = _make_service(trino=trino)
    begin = datetime(2026, 9, 1, 6, 0, tzinfo=UTC)
    end = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)

    result = service._select_flights_for_query(  # noqa: SLF001
        FlightQuerySpecEntity(airport="LFBO"), begin, end, quota=5,
    )

    assert result is None


def test_select_flights_for_query_returns_none_on_trino_error() -> None:
    """ """
    trino = _FakeTrino(flightlist_error=TrinoError("boom"))
    service = _make_service(trino=trino)
    begin = datetime(2026, 9, 1, 6, 0, tzinfo=UTC)
    end = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)

    result = service._select_flights_for_query(  # noqa: SLF001
        FlightQuerySpecEntity(airport="LFBO"), begin, end, quota=5,
    )

    assert result is None


def test_select_flights_for_query_returns_none_when_no_valid_flights() -> None:
    """ """
    invalid_df = pd.DataFrame(
        {
            "icao24": [None],
            "firstseen": [1000.0],
            "lastseen": [2000.0],
            "departure": ["LFBO"],
            "arrival": ["LFPG"],
            "callsign": ["AFR123"],
        },
    )
    trino = _FakeTrino(flightlist_df=invalid_df)
    service = _make_service(trino=trino)
    begin = datetime(2026, 9, 1, 6, 0, tzinfo=UTC)
    end = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)

    result = service._select_flights_for_query(  # noqa: SLF001
        FlightQuerySpecEntity(airport="LFBO"), begin, end, quota=5,
    )

    assert result is None


# ============================================================================
# TESTS — _fetch_combined_history
# ============================================================================
def _valid_history_df() -> pd.DataFrame:
    """ """
    return pd.DataFrame(
        {
            "icao24": ["3944ef", "3944ef"],
            "time": [1500.0, 1200.0],
            "lat": [43.0, 43.5],
            "lon": [1.0, 1.5],
            "baroaltitude": [1000.0, 2000.0],
            "onground": [False, False],
            "velocity": [200.0, 220.0],
            "vertrate": [0.0, 1.0],
        },
    )


def test_fetch_combined_history_sorts_by_time() -> None:
    """ """
    trino = _FakeTrino(history_df=_valid_history_df())
    service = _make_service(trino=trino)
    flights_df = pd.DataFrame({"icao24": ["3944ef"], "firstseen": [1000.0], "lastseen": [2000.0]})

    result = service._fetch_combined_history(flights_df)  # noqa: SLF001

    assert result is not None
    assert result["time_unix"].tolist() == [1200.0, 1500.0]


def test_fetch_combined_history_returns_none_on_trino_error() -> None:
    """ """
    trino = _FakeTrino(history_error=TrinoError("boom"))
    service = _make_service(trino=trino)
    flights_df = pd.DataFrame({"icao24": ["3944ef"], "firstseen": [1000.0], "lastseen": [2000.0]})

    assert service._fetch_combined_history(flights_df) is None  # noqa: SLF001


def test_fetch_combined_history_returns_none_on_empty_result() -> None:
    """ """
    trino = _FakeTrino(history_df=pd.DataFrame())
    service = _make_service(trino=trino)
    flights_df = pd.DataFrame({"icao24": ["3944ef"], "firstseen": [1000.0], "lastseen": [2000.0]})

    assert service._fetch_combined_history(flights_df) is None  # noqa: SLF001


# ============================================================================
# TESTS — _build_aircraft_for_flight
# ============================================================================
def test_build_aircraft_for_flight_returns_none_without_history() -> None:
    """ """
    service = _make_service()
    flight_row = pd.Series({"icao24": "3944ef", "firstseen": 1000.0, "lastseen": 2000.0, "callsign": "AFR123"})

    result = service._build_aircraft_for_flight(flight_row, {}, reference_time=1000.0)  # noqa: SLF001

    assert result is None


def test_build_aircraft_for_flight_returns_none_with_too_few_points() -> None:
    """ """
    service = _make_service()
    flight_row = pd.Series({"icao24": "3944ef", "firstseen": 1000.0, "lastseen": 2000.0, "callsign": "AFR123"})
    history = pd.DataFrame(
        {
            "icao24": ["3944ef"],
            "time_unix": [1500.0],
            "lat": [43.0],
            "lon": [1.0],
            "baroaltitude": [1000.0],
            "onground": [False],
            "velocity": [200.0],
            "vertrate": [0.0],
        },
    )

    result = service._build_aircraft_for_flight(  # noqa: SLF001
        flight_row, {"3944ef": history}, reference_time=1000.0,
    )

    assert result is None


def test_build_aircraft_for_flight_builds_valid_aircraft() -> None:
    """ """
    known_airport = AirportEntity.unknown()
    known_airport.icao = "LFBO"
    metadata = AircraftMetadataEntity(
        registration="F-GKXA", manufacturer="AIRBUS", model="A320", typecode="A320", operator="AIR FRANCE",
    )
    service = _make_service(
        airport_service=_FakeAirportService({"LFBO": known_airport}),
        aircraft_database_service=_FakeAircraftDatabaseService({"3944ef": metadata}),
    )
    flight_row = pd.Series(
        {
            "icao24": "3944ef",
            "firstseen": 1000.0,
            "lastseen": 2000.0,
            "callsign": "  AFR123  ",
            "departure": "LFBO",
            "arrival": "ZZZZ",
        },
    )
    history = pd.DataFrame(
        {
            "icao24": ["3944ef", "3944ef"],
            "time_unix": [1000.0, 2000.0],
            "lat": [43.0, 44.0],
            "lon": [1.0, 2.0],
            "baroaltitude": [304.8, 609.6],
            "onground": [True, False],
            "velocity": [0.0, 100.0],
            "vertrate": [0.0, float("nan")],
        },
    )

    aircraft = service._build_aircraft_for_flight(  # noqa: SLF001
        flight_row, {"3944ef": history}, reference_time=1000.0,
    )

    assert aircraft is not None
    assert aircraft.callsign == "AFR123"
    assert aircraft.origin_airport.icao == "LFBO"
    assert aircraft.destination_airport.icao == "????"
    assert aircraft.metadata is not None
    assert aircraft.metadata.typecode == "A320"
    assert aircraft.trajectory.get_first_point_state()[2] == pytest.approx(1000.0)  # 304.8m -> 1000ft


def test_build_aircraft_for_flight_defaults_callsign_when_missing() -> None:
    """ """
    service = _make_service()
    flight_row = pd.Series({"icao24": "3944ef", "firstseen": 1000.0, "lastseen": 2000.0})
    history = pd.DataFrame(
        {
            "icao24": ["3944ef", "3944ef"],
            "time_unix": [1000.0, 2000.0],
            "lat": [43.0, 44.0],
            "lon": [1.0, 2.0],
            "baroaltitude": [1000.0, 2000.0],
            "onground": [True, False],
            "velocity": [0.0, 100.0],
            "vertrate": [0.0, 0.0],
        },
    )

    aircraft = service._build_aircraft_for_flight(  # noqa: SLF001
        flight_row, {"3944ef": history}, reference_time=1000.0,
    )

    assert aircraft is not None
    assert aircraft.callsign == "UNKNOWN"


# ============================================================================
# TESTS — import_fleet_for_period (end-to-end with fakes)
# ============================================================================
def test_import_fleet_for_period_returns_empty_without_query_specs() -> None:
    """ """
    service = _make_service()

    fleet = service.import_fleet_for_period(
        begin=datetime(2026, 9, 1, 6, 0, tzinfo=UTC), end=datetime(2026, 9, 1, 8, 0, tzinfo=UTC),
    )

    assert fleet == []


def test_import_fleet_for_period_builds_fleet_end_to_end() -> None:
    """ """
    trino = _FakeTrino(flightlist_df=_valid_flightlist_df(), history_df=_valid_history_df())
    service = _make_service(trino=trino)

    fleet = service.import_fleet_for_period(
        begin=datetime(1970, 1, 1, 0, 16, 40, tzinfo=UTC),  # timestamp = 1000.0
        end=datetime(1970, 1, 1, 0, 33, 20, tzinfo=UTC),
        max_flights=5,
        airports=["LFBO"],
    )

    assert len(fleet) == 1
    assert fleet[0].callsign == "AFR123"


def test_import_fleet_for_period_returns_empty_when_selection_fails() -> None:
    """ """
    trino = _FakeTrino(flightlist_df=pd.DataFrame())
    service = _make_service(trino=trino)

    fleet = service.import_fleet_for_period(
        begin=datetime(2026, 9, 1, 6, 0, tzinfo=UTC), end=datetime(2026, 9, 1, 8, 0, tzinfo=UTC),
        airports=["LFBO"],
    )

    assert fleet == []


def test_import_fleet_for_period_returns_empty_when_history_empty() -> None:
    """ """
    trino = _FakeTrino(flightlist_df=_valid_flightlist_df(), history_df=pd.DataFrame())
    service = _make_service(trino=trino)

    fleet = service.import_fleet_for_period(
        begin=datetime(2026, 9, 1, 6, 0, tzinfo=UTC), end=datetime(2026, 9, 1, 8, 0, tzinfo=UTC),
        airports=["LFBO"],
    )

    assert fleet == []


def test_import_fleet_for_period_skips_zero_quota_specs(monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    import random as random_module

    monkeypatch.setattr(random_module, "sample", lambda population, k: list(population)[:k])

    trino = _FakeTrino(flightlist_df=_valid_flightlist_df(), history_df=_valid_history_df())
    service = _make_service(trino=trino)

    fleet = service.import_fleet_for_period(
        begin=datetime(1970, 1, 1, 0, 16, 40, tzinfo=UTC),
        end=datetime(1970, 1, 1, 0, 33, 20, tzinfo=UTC),
        max_flights=1,
        airports=["LFBO", "LFPG"],
    )

    # quotas = [1, 0] with the deterministic sample above -> only LFBO is queried.
    assert len(trino.flightlist_calls) == 1
    assert len(fleet) == 1
