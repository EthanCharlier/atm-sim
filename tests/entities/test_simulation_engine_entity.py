""" """

# ============================================================================
# IMPORT
# ============================================================================
import pytest

# ENTITIES IMPORT
from atm_sim.entities.aircraft_entity import AircraftEntity
from atm_sim.entities.airport_entity import AirportEntity
from atm_sim.entities.clock_entity import SimClockEntity
from atm_sim.entities.simulation_engine_entity import SimulationEngineEntity
from atm_sim.entities.trajectory_entity import TrajectoryEntity
from atm_sim.entities.trajectory_point_entity import TrajectoryPointEntity

# ENUMS IMPORT
from atm_sim.enums.aircraft_status_enum import AircraftStatusEnum
from atm_sim.enums.simulation_status_enum import SimulationStatusEnum


# ============================================================================
# HELPERS
# ============================================================================
def _make_aircraft(start: float, end: float) -> AircraftEntity:
    """ """
    points = [
        TrajectoryPointEntity(
            time_offset_seconds=start,
            lat=0.0,
            lon=0.0,
            altitude_ft=0.0,
            ground_speed_kmh=0.0,
            vertical_rate_ft_per_min=0.0,
            on_ground=True,
        ),
        TrajectoryPointEntity(
            time_offset_seconds=end,
            lat=1.0,
            lon=1.0,
            altitude_ft=1000.0,
            ground_speed_kmh=500.0,
            vertical_rate_ft_per_min=0.0,
            on_ground=False,
        ),
    ]
    trajectory = TrajectoryEntity(points=points)
    return AircraftEntity(
        callsign="AFR123",
        origin_airport=AirportEntity.unknown(),
        destination_airport=AirportEntity.unknown(),
        trajectory=trajectory,
    )


# ============================================================================
# TESTS
# ============================================================================
def test_add_aircraft_appends_to_fleet() -> None:
    """ """
    engine = SimulationEngineEntity(clock=SimClockEntity(tick_seconds=1.0))
    aircraft = _make_aircraft(0.0, 10.0)

    engine.add_aircraft(aircraft)

    assert engine.fleet == [aircraft]


def test_tick_advances_clock_and_updates_fleet() -> None:
    """ """
    engine = SimulationEngineEntity(clock=SimClockEntity(tick_seconds=5.0))
    aircraft = _make_aircraft(0.0, 10.0)
    engine.add_aircraft(aircraft)

    engine.tick()

    assert engine.clock.sim_time_elapsed == pytest.approx(5.0)
    assert aircraft.status == AircraftStatusEnum.IN_FLIGHT


def test_get_status_running_before_duration_elapsed() -> None:
    """ """
    engine = SimulationEngineEntity(clock=SimClockEntity(tick_seconds=1.0))

    assert engine.get_status(total_duration_seconds=100.0) == SimulationStatusEnum.RUNNING


def test_get_status_complete_once_duration_elapsed() -> None:
    """ """
    engine = SimulationEngineEntity(clock=SimClockEntity(tick_seconds=100.0))

    engine.tick()

    assert engine.get_status(total_duration_seconds=100.0) == SimulationStatusEnum.COMPLETE
