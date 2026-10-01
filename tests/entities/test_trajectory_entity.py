""" """

# ============================================================================
# IMPORT
# ============================================================================
import pytest

# ENTITIES IMPORT
from atm_sim.entities.trajectory_entity import TrajectoryEntity
from atm_sim.entities.trajectory_point_entity import TrajectoryPointEntity


# ============================================================================
# HELPERS
# ============================================================================
def _make_trajectory() -> TrajectoryEntity:
    """ """
    points = [
        TrajectoryPointEntity(
            time_offset_seconds=0.0,
            lat=43.0,
            lon=1.0,
            altitude_ft=1000.0,
            ground_speed_kmh=200.0,
            vertical_rate_ft_per_min=1500.0,
            on_ground=True,
        ),
        TrajectoryPointEntity(
            time_offset_seconds=100.0,
            lat=44.0,
            lon=2.0,
            altitude_ft=20000.0,
            ground_speed_kmh=600.0,
            vertical_rate_ft_per_min=0.0,
            on_ground=False,
        ),
        TrajectoryPointEntity(
            time_offset_seconds=200.0,
            lat=45.0,
            lon=3.0,
            altitude_ft=500.0,
            ground_speed_kmh=150.0,
            vertical_rate_ft_per_min=-1200.0,
            on_ground=True,
        ),
    ]
    return TrajectoryEntity(points=points)


# ============================================================================
# TESTS — construction
# ============================================================================
def test_requires_at_least_two_points() -> None:
    """ """
    single_point = [
        TrajectoryPointEntity(
            time_offset_seconds=0.0,
            lat=0.0,
            lon=0.0,
            altitude_ft=0.0,
            ground_speed_kmh=0.0,
            vertical_rate_ft_per_min=0.0,
            on_ground=True,
        ),
    ]

    with pytest.raises(ValueError, match="at least 2 points"):
        TrajectoryEntity(points=single_point)


def test_start_and_end_time_match_first_and_last_point() -> None:
    """ """
    trajectory = _make_trajectory()

    assert trajectory.start_time_seconds == pytest.approx(0.0)
    assert trajectory.end_time_seconds == pytest.approx(200.0)


# ============================================================================
# TESTS — has_started_at / has_arrived_at
# ============================================================================
def test_has_started_at_boundaries() -> None:
    """ """
    trajectory = _make_trajectory()

    assert trajectory.has_started_at(-1.0) is False
    assert trajectory.has_started_at(0.0) is True
    assert trajectory.has_started_at(50.0) is True


def test_has_arrived_at_boundaries() -> None:
    """ """
    trajectory = _make_trajectory()

    assert trajectory.has_arrived_at(199.0) is False
    assert trajectory.has_arrived_at(200.0) is True
    assert trajectory.has_arrived_at(500.0) is True


# ============================================================================
# TESTS — first/last point state
# ============================================================================
def test_get_first_point_state() -> None:
    """ """
    trajectory = _make_trajectory()

    assert trajectory.get_first_point_state() == pytest.approx((43.0, 1.0, 1000.0))


def test_get_last_point_state() -> None:
    """ """
    trajectory = _make_trajectory()

    assert trajectory.get_last_point_state() == pytest.approx((45.0, 3.0, 500.0))


# ============================================================================
# TESTS — get_position_at
# ============================================================================
def test_get_position_at_before_start_returns_first_point() -> None:
    """ """
    trajectory = _make_trajectory()

    assert trajectory.get_position_at(-50.0) == pytest.approx(trajectory.get_first_point_state())


def test_get_position_at_after_end_returns_last_point() -> None:
    """ """
    trajectory = _make_trajectory()

    assert trajectory.get_position_at(9999.0) == pytest.approx(trajectory.get_last_point_state())


def test_get_position_at_midsegment_interpolates() -> None:
    """ """
    trajectory = _make_trajectory()

    lat, lon, altitude_ft = trajectory.get_position_at(50.0)

    assert (lat, lon) == pytest.approx((43.5, 1.5))
    assert altitude_ft == pytest.approx(10500.0)


# ============================================================================
# TESTS — get_in_flight_state_at
# ============================================================================
def test_get_in_flight_state_at_clamps_before_start() -> None:
    """ """
    trajectory = _make_trajectory()

    lat, lon, altitude_ft, ground_speed_kmh, vertical_rate = trajectory.get_in_flight_state_at(-100.0)

    assert (lat, lon, altitude_ft) == pytest.approx((43.0, 1.0, 1000.0))
    assert ground_speed_kmh == pytest.approx(200.0)
    assert vertical_rate == pytest.approx(1500.0)


def test_get_in_flight_state_at_interpolates_second_segment() -> None:
    """ """
    trajectory = _make_trajectory()

    _, _, altitude_ft, ground_speed_kmh, vertical_rate = trajectory.get_in_flight_state_at(150.0)

    assert altitude_ft == pytest.approx(10250.0)
    assert ground_speed_kmh == pytest.approx(375.0)
    assert vertical_rate == pytest.approx(-600.0)


# ============================================================================
# TESTS — max altitude / speed (full trajectory)
# ============================================================================
def test_get_max_altitude_ft() -> None:
    """ """
    assert _make_trajectory().get_max_altitude_ft() == pytest.approx(20000.0)


def test_get_max_ground_speed_kmh() -> None:
    """ """
    assert _make_trajectory().get_max_ground_speed_kmh() == pytest.approx(600.0)


# ============================================================================
# TESTS — max altitude / speed bounded by elapsed time
# ============================================================================
def test_get_max_altitude_ft_until_before_peak() -> None:
    """ """
    trajectory = _make_trajectory()

    # Only the first point (1000 ft) has been reached at t=0.
    assert trajectory.get_max_altitude_ft_until(0.0) == pytest.approx(1000.0)


def test_get_max_altitude_ft_until_after_peak() -> None:
    """ """
    trajectory = _make_trajectory()

    assert trajectory.get_max_altitude_ft_until(150.0) == pytest.approx(20000.0)


def test_get_max_ground_speed_kmh_until_clamps_to_waiting_state() -> None:
    """ """
    trajectory = _make_trajectory()

    # Before the trajectory starts, only the first point counts.
    assert trajectory.get_max_ground_speed_kmh_until(-50.0) == pytest.approx(200.0)


def test_get_max_ground_speed_kmh_until_full_range() -> None:
    """ """
    trajectory = _make_trajectory()

    assert trajectory.get_max_ground_speed_kmh_until(9999.0) == pytest.approx(600.0)


# ============================================================================
# TESTS — duration
# ============================================================================
def test_get_duration_seconds() -> None:
    """ """
    assert _make_trajectory().get_duration_seconds() == pytest.approx(200.0)


# ============================================================================
# TESTS — zero-duration segment (duplicate timestamps)
# ============================================================================
def test_get_in_flight_state_at_handles_zero_duration_segment() -> None:
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
            time_offset_seconds=50.0,
            lat=10.0,
            lon=10.0,
            altitude_ft=1000.0,
            ground_speed_kmh=300.0,
            vertical_rate_ft_per_min=500.0,
            on_ground=False,
        ),
        TrajectoryPointEntity(
            time_offset_seconds=50.0,
            lat=20.0,
            lon=20.0,
            altitude_ft=2000.0,
            ground_speed_kmh=400.0,
            vertical_rate_ft_per_min=-500.0,
            on_ground=False,
        ),
    ]
    trajectory = TrajectoryEntity(points=points)

    lat, lon, altitude_ft, ground_speed_kmh, vertical_rate = trajectory.get_in_flight_state_at(50.0)

    assert (lat, lon, altitude_ft) == pytest.approx((10.0, 10.0, 1000.0))
    assert ground_speed_kmh == pytest.approx(300.0)
    assert vertical_rate == pytest.approx(500.0)
