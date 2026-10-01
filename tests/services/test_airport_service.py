""" """

# ============================================================================
# IMPORT
# ============================================================================

# SERVICES IMPORT
from atm_sim.services.airport_service import AirportService


# ============================================================================
# TESTS
# ============================================================================
def test_get_airport_returns_known_airport() -> None:
    """ """
    service = AirportService()

    airport = service.get_airport("LFBO")

    assert airport is not None
    assert airport.icao == "LFBO"
    assert airport.city == "Toulouse/Blagnac"


def test_get_airport_is_case_insensitive() -> None:
    """ """
    service = AirportService()

    airport = service.get_airport("lfbo")

    assert airport is not None
    assert airport.icao == "LFBO"


def test_get_airport_returns_none_for_unknown_code() -> None:
    """ """
    service = AirportService()

    assert service.get_airport("ZZZZ") is None
