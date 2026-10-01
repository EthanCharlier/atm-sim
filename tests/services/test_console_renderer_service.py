""" """

# ============================================================================
# IMPORT
# ============================================================================
from datetime import UTC, datetime

# ENTITIES IMPORT
from atm_sim.entities.aircraft_entity import AircraftEntity
from atm_sim.entities.aircraft_statistics_entity import AircraftStatisticsEntity
from atm_sim.entities.airport_entity import AirportEntity
from atm_sim.entities.clock_entity import SimClockEntity
from atm_sim.entities.simulation_engine_entity import SimulationEngineEntity
from atm_sim.entities.simulation_statistics_entity import SimulationStatisticsEntity
from atm_sim.entities.trajectory_entity import TrajectoryEntity
from atm_sim.entities.trajectory_point_entity import TrajectoryPointEntity

# ENUMS IMPORT
from atm_sim.enums.aircraft_status_enum import AircraftStatusEnum
from atm_sim.enums.simulation_status_enum import SimulationStatusEnum

# SERVICES IMPORT
from atm_sim.services.console_renderer_service import ConsoleRendererService


# ============================================================================
# HELPERS
# ============================================================================
def _make_airport(icao: str) -> AirportEntity:
    """ """
    return AirportEntity(
        icao=icao,
        iata=icao[1:],
        name=f"{icao} Airport",
        city="City",
        country="FR",
        lat=0.0,
        lon=0.0,
        elevation_ft=0.0,
        timezone="UTC",
    )


def _make_aircraft(callsign: str = "AFR123") -> AircraftEntity:
    """ """
    points = [
        TrajectoryPointEntity(
            time_offset_seconds=0.0,
            lat=43.0,
            lon=1.0,
            altitude_ft=1000.0,
            ground_speed_kmh=300.0,
            vertical_rate_ft_per_min=500.0,
            on_ground=False,
        ),
        TrajectoryPointEntity(
            time_offset_seconds=100.0,
            lat=44.0,
            lon=2.0,
            altitude_ft=2000.0,
            ground_speed_kmh=400.0,
            vertical_rate_ft_per_min=0.0,
            on_ground=False,
        ),
    ]
    trajectory = TrajectoryEntity(points=points)
    return AircraftEntity(
        callsign=callsign,
        origin_airport=_make_airport("LFBO"),
        destination_airport=_make_airport("LFPG"),
        trajectory=trajectory,
    )


# ============================================================================
# TESTS — reserve_space
# ============================================================================
def test_reserve_space_prints_expected_blank_lines(capsys: object) -> None:
    """ """
    ConsoleRendererService.reserve_space(fleet_size=3)

    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert captured.out.count("\n") == 3 + 7 + 1


# ============================================================================
# TESTS — render
# ============================================================================
def test_render_includes_header_and_fleet_row(capsys: object) -> None:
    """ """
    engine = SimulationEngineEntity(clock=SimClockEntity(tick_seconds=1.0))
    aircraft = _make_aircraft()
    engine.add_aircraft(aircraft)

    ConsoleRendererService.render(
        engine=engine,
        airport_label="LFBO",
        begin=datetime(2026, 9, 1, 6, 0, tzinfo=UTC),
        status=SimulationStatusEnum.RUNNING,
    )

    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert "LFBO" in captured.out
    assert "CALLSIGN" in captured.out
    assert "AFR123" in captured.out
    assert "?" in captured.out  # no metadata -> type_code fallback


def test_render_with_empty_fleet_still_prints_header(capsys: object) -> None:
    """ """
    engine = SimulationEngineEntity(clock=SimClockEntity(tick_seconds=1.0))

    ConsoleRendererService.render(
        engine=engine,
        airport_label="LFBO",
        begin=datetime(2026, 9, 1, 6, 0, tzinfo=UTC),
        status=SimulationStatusEnum.PAUSED,
    )

    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert "[paused]" in captured.out
    assert "0 in flight" in captured.out


# ============================================================================
# TESTS — render_summary
# ============================================================================
def test_render_summary_includes_header_and_aircraft_row(capsys: object) -> None:
    """ """
    aircraft_stats = AircraftStatisticsEntity(
        callsign="AFR123",
        origin_icao="LFBO",
        destination_icao="LFPG",
        type_code="A320",
        status=AircraftStatusEnum.ARRIVED,
        progress_percent=100.0,
        elapsed_seconds=600.0,
        max_altitude_ft=35000.0,
        max_ground_speed_kmh=800.0,
    )
    statistics = SimulationStatisticsEntity(
        per_aircraft=[aircraft_stats],
        total_flights=1,
        average_duration_seconds=600.0,
        max_altitude_ft=35000.0,
        max_ground_speed_kmh=800.0,
    )

    ConsoleRendererService.render_summary(
        airport_label="LFBO",
        begin=datetime(2026, 9, 1, 6, 0, tzinfo=UTC),
        end=datetime(2026, 9, 1, 8, 0, tzinfo=UTC),
        statistics=statistics,
    )

    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert "OpenSky ATM Simulation summary" in captured.out
    assert "LFBO" in captured.out
    assert "AFR123" in captured.out
    assert "1 flight(s)" in captured.out
