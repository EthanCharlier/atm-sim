""" """

# ============================================================================
# IMPORT
# ============================================================================
import pytest

# ENTITIES IMPORT
from atm_sim.entities.aircraft_entity import AircraftEntity
from atm_sim.entities.airport_entity import AirportEntity
from atm_sim.entities.trajectory_entity import TrajectoryEntity
from atm_sim.entities.trajectory_point_entity import TrajectoryPointEntity
from atm_sim.enums.aircraft_status_enum import AircraftStatusEnum


# ============================================================================
# HELPERS
# ============================================================================
def _make_aircraft() -> AircraftEntity:
    """ """
    points = [
        TrajectoryPointEntity(
            time_offset_seconds=50.0,
            lat=0.0,
            lon=0.0,
            altitude_ft=0.0,
            ground_speed_kmh=0.0,
            vertical_rate_ft_per_min=0.0,
            on_ground=True,
        ),
        TrajectoryPointEntity(
            time_offset_seconds=150.0,
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
# TESTS — initial state
# ============================================================================
def test_initial_state_is_waiting() -> None:
    """ """
    aircraft = _make_aircraft()

    assert aircraft.status == AircraftStatusEnum.WAITING
    assert aircraft.get_progress_percent(0.0) == pytest.approx(0.0)
    assert aircraft.current_ground_speed_kmh == pytest.approx(0.0)


# ============================================================================
# TESTS — in-flight
# ============================================================================
def test_update_mid_flight_sets_in_flight_status() -> None:
    """ """
    aircraft = _make_aircraft()

    aircraft.update(100.0)

    assert aircraft.status == AircraftStatusEnum.IN_FLIGHT
    assert aircraft.get_progress_percent(100.0) == pytest.approx(50.0)
    assert aircraft.current_ground_speed_kmh == pytest.approx(250.0)


# ============================================================================
# TESTS — arrived
# ============================================================================
def test_update_after_end_sets_arrived_status() -> None:
    """ """
    aircraft = _make_aircraft()

    aircraft.update(200.0)

    assert aircraft.status == AircraftStatusEnum.ARRIVED
    assert aircraft.get_progress_percent(200.0) == pytest.approx(100.0)
    assert aircraft.current_ground_speed_kmh == pytest.approx(0.0)
    assert (aircraft.current_lat, aircraft.current_lon) == pytest.approx((1.0, 1.0))


# ============================================================================
# TESTS — short-circuit branches
# ============================================================================
def test_repeated_update_while_still_waiting_is_a_noop() -> None:
    """ """
    aircraft = _make_aircraft()

    aircraft.update(10.0)
    aircraft.update(20.0)

    assert aircraft.status == AircraftStatusEnum.WAITING
    assert (aircraft.current_lat, aircraft.current_lon) == pytest.approx((0.0, 0.0))


def test_repeated_update_while_still_arrived_is_a_noop() -> None:
    """ """
    aircraft = _make_aircraft()

    aircraft.update(160.0)
    aircraft.update(170.0)

    assert aircraft.status == AircraftStatusEnum.ARRIVED
    assert (aircraft.current_lat, aircraft.current_lon) == pytest.approx((1.0, 1.0))


# ============================================================================
# TESTS — defensive branch (unreachable via normal status flow)
# ============================================================================
def test_get_progress_percent_handles_zero_duration_trajectory() -> None:
    """ """
    points = [
        TrajectoryPointEntity(
            time_offset_seconds=50.0,
            lat=0.0,
            lon=0.0,
            altitude_ft=0.0,
            ground_speed_kmh=0.0,
            vertical_rate_ft_per_min=0.0,
            on_ground=True,
        ),
        TrajectoryPointEntity(
            time_offset_seconds=50.0,
            lat=1.0,
            lon=1.0,
            altitude_ft=1000.0,
            ground_speed_kmh=500.0,
            vertical_rate_ft_per_min=0.0,
            on_ground=False,
        ),
    ]
    trajectory = TrajectoryEntity(points=points)
    aircraft = AircraftEntity(
        callsign="AFR123",
        origin_airport=AirportEntity.unknown(),
        destination_airport=AirportEntity.unknown(),
        trajectory=trajectory,
    )
    # Force a status the normal update() flow can never reach with a
    # zero-duration trajectory, to exercise the defensive guard.
    aircraft.status = AircraftStatusEnum.IN_FLIGHT

    assert aircraft.get_progress_percent(50.0) == pytest.approx(0.0)
