""" """

# ============================================================================
# IMPORT
# ============================================================================
import pytest

# ENTITIES IMPORT
from atm_sim.entities.clock_entity import SimClockEntity, resolve_speed_index

# ENUMS IMPORT
from atm_sim.enums.simulation_status_enum import SimulationStatusEnum


# ============================================================================
# TESTS — resolve_speed_index
# ============================================================================
@pytest.mark.parametrize(
    ("value", "expected_index"),
    [
        (-3600, 0),
        (1, 3),
        (3600, 6),
        (0, 3),
    ],
)
def test_resolve_speed_index(value: float, expected_index: int) -> None:
    """ """
    assert resolve_speed_index(value) == expected_index


# ============================================================================
# TESTS — speed_factor / advance
# ============================================================================
def test_default_speed_factor_is_realtime() -> None:
    """ """
    clock = SimClockEntity(tick_seconds=1.0)

    assert clock.speed_factor == pytest.approx(1.0)


def test_advance_increases_elapsed_time_forward() -> None:
    """ """
    clock = SimClockEntity(tick_seconds=1.0)

    clock.advance()
    clock.advance()

    assert clock.sim_time_elapsed == pytest.approx(2.0)


def test_advance_does_nothing_when_paused() -> None:
    """ """
    clock = SimClockEntity(tick_seconds=1.0)

    clock.pause()
    clock.advance()

    assert clock.sim_time_elapsed == pytest.approx(0.0)
    assert clock.is_paused() is True


def test_resume_allows_advance_again() -> None:
    """ """
    clock = SimClockEntity(tick_seconds=1.0)

    clock.pause()
    clock.resume()
    clock.advance()

    assert clock.sim_time_elapsed == pytest.approx(1.0)
    assert clock.is_paused() is False


def test_advance_backward_clamps_at_zero() -> None:
    """ """
    clock = SimClockEntity(tick_seconds=1.0)

    for _ in range(3):
        clock.decrease_speed()  # index 3 -> 0, speed_factor becomes negative

    clock.advance()

    assert clock.sim_time_elapsed == pytest.approx(0.0)


# ============================================================================
# TESTS — speed index bounds
# ============================================================================
def test_increase_speed_clamps_at_max_index() -> None:
    """ """
    clock = SimClockEntity(tick_seconds=1.0)

    for _ in range(10):
        clock.increase_speed()

    assert clock.speed_factor == pytest.approx(3600.0)


def test_decrease_speed_clamps_at_min_index() -> None:
    """ """
    clock = SimClockEntity(tick_seconds=1.0)

    for _ in range(10):
        clock.decrease_speed()

    assert clock.speed_factor == pytest.approx(-3600.0)


# ============================================================================
# TESTS — get_status
# ============================================================================
def test_get_status_complete_takes_priority() -> None:
    """ """
    clock = SimClockEntity(tick_seconds=1.0)
    clock.pause()

    assert clock.get_status(is_complete=True) == SimulationStatusEnum.COMPLETE


def test_get_status_paused() -> None:
    """ """
    clock = SimClockEntity(tick_seconds=1.0)
    clock.pause()

    assert clock.get_status(is_complete=False) == SimulationStatusEnum.PAUSED


def test_get_status_running() -> None:
    """ """
    clock = SimClockEntity(tick_seconds=1.0)

    assert clock.get_status(is_complete=False) == SimulationStatusEnum.RUNNING
