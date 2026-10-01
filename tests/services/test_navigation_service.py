""" """

# ============================================================================
# IMPORT
# ============================================================================
import pytest

# SERVICES IMPORT
from atm_sim.services.navigation_service import NavigationService


# ============================================================================
# TESTS — compute_distance_meters
# ============================================================================
def test_compute_distance_meters_same_point_is_zero() -> None:
    """ """
    distance = NavigationService.compute_distance_meters(43.6291, 1.3616, 43.6291, 1.3616)

    assert distance == pytest.approx(0.0, abs=1e-6)


def test_compute_distance_meters_known_distance() -> None:
    """ """
    # Toulouse-Blagnac (LFBO) to Paris-Orly (LFPO), ~572 km great-circle.
    distance = NavigationService.compute_distance_meters(43.6291, 1.3616, 48.7262, 2.3650)

    assert distance == pytest.approx(572_000, rel=0.01)


def test_compute_distance_meters_is_symmetric() -> None:
    """ """
    forward = NavigationService.compute_distance_meters(43.6291, 1.3616, 48.7262, 2.3650)
    backward = NavigationService.compute_distance_meters(48.7262, 2.3650, 43.6291, 1.3616)

    assert forward == pytest.approx(backward)


# ============================================================================
# TESTS — compute_intermediate_position
# ============================================================================
def test_compute_intermediate_position_at_start() -> None:
    """ """
    lat, lon = NavigationService.compute_intermediate_position(0.0, 0.0, 10.0, 10.0, 0.0)

    assert (lat, lon) == pytest.approx((0.0, 0.0))


def test_compute_intermediate_position_at_end() -> None:
    """ """
    lat, lon = NavigationService.compute_intermediate_position(0.0, 0.0, 10.0, 10.0, 1.0)

    assert (lat, lon) == pytest.approx((10.0, 10.0))


def test_compute_intermediate_position_at_midpoint() -> None:
    """ """
    lat, lon = NavigationService.compute_intermediate_position(0.0, 0.0, 10.0, 20.0, 0.5)

    assert (lat, lon) == pytest.approx((5.0, 10.0))


@pytest.mark.parametrize("fraction", [-1.0, 2.0])
def test_compute_intermediate_position_clamps_out_of_range_fraction(fraction: float) -> None:
    """ """
    lat, lon = NavigationService.compute_intermediate_position(0.0, 0.0, 10.0, 10.0, fraction)

    expected = (0.0, 0.0) if fraction < 0 else (10.0, 10.0)
    assert (lat, lon) == pytest.approx(expected)


# ============================================================================
# TESTS — compute_intermediate_value
# ============================================================================
def test_compute_intermediate_value_at_start() -> None:
    """ """
    assert NavigationService.compute_intermediate_value(100.0, 200.0, 0.0) == pytest.approx(100.0)


def test_compute_intermediate_value_at_end() -> None:
    """ """
    assert NavigationService.compute_intermediate_value(100.0, 200.0, 1.0) == pytest.approx(200.0)


def test_compute_intermediate_value_at_midpoint() -> None:
    """ """
    assert NavigationService.compute_intermediate_value(100.0, 200.0, 0.5) == pytest.approx(150.0)


@pytest.mark.parametrize("fraction", [-0.5, 1.5])
def test_compute_intermediate_value_clamps_out_of_range_fraction(fraction: float) -> None:
    """ """
    result = NavigationService.compute_intermediate_value(100.0, 200.0, fraction)

    expected = 100.0 if fraction < 0 else 200.0
    assert result == pytest.approx(expected)
