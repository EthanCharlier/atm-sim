""" """

# ============================================================================
# IMPORT
# ============================================================================

# ENTITIES IMPORT
from atm_sim.entities.aircraft_metadata_entity import AircraftMetadataEntity
from atm_sim.entities.aircraft_statistics_entity import AircraftStatisticsEntity
from atm_sim.entities.airport_entity import AirportEntity
from atm_sim.entities.flight_query_spec_entity import FlightQuerySpecEntity
from atm_sim.entities.simulation_statistics_entity import SimulationStatisticsEntity

# ENUMS IMPORT
from atm_sim.enums.aircraft_status_enum import AircraftStatusEnum


# ============================================================================
# TESTS — AirportEntity
# ============================================================================
def test_airport_entity_unknown_factory() -> None:
    """ """
    airport = AirportEntity.unknown()

    assert airport.icao == "????"
    assert airport.lat == 0.0
    assert airport.lon == 0.0


# ============================================================================
# TESTS — AircraftMetadataEntity
# ============================================================================
def test_aircraft_metadata_entity_stores_fields() -> None:
    """ """
    metadata = AircraftMetadataEntity(
        registration="F-GKXA",
        manufacturer="AIRBUS",
        model="A320",
        typecode="A320",
        operator="AIR FRANCE",
    )

    assert metadata.registration == "F-GKXA"
    assert metadata.typecode == "A320"


# ============================================================================
# TESTS — FlightQuerySpecEntity
# ============================================================================
def test_flight_query_spec_entity_defaults_to_none() -> None:
    """ """
    spec = FlightQuerySpecEntity()

    assert spec.airport is None
    assert spec.callsign is None


def test_flight_query_spec_entity_stores_fields() -> None:
    """ """
    spec = FlightQuerySpecEntity(airport="LFBO", callsign="AFR123")

    assert spec.airport == "LFBO"
    assert spec.callsign == "AFR123"


# ============================================================================
# TESTS — AircraftStatisticsEntity / SimulationStatisticsEntity
# ============================================================================
def test_aircraft_statistics_entity_stores_fields() -> None:
    """ """
    stats = AircraftStatisticsEntity(
        callsign="AFR123",
        origin_icao="LFBO",
        destination_icao="LFPG",
        type_code="A320",
        status=AircraftStatusEnum.IN_FLIGHT,
        progress_percent=50.0,
        elapsed_seconds=300.0,
        max_altitude_ft=35000.0,
        max_ground_speed_kmh=800.0,
    )

    assert stats.callsign == "AFR123"
    assert stats.status == AircraftStatusEnum.IN_FLIGHT
    assert stats.max_altitude_ft == 35000.0


def test_simulation_statistics_entity_stores_fields() -> None:
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

    stats = SimulationStatisticsEntity(
        per_aircraft=[aircraft_stats],
        total_flights=1,
        average_duration_seconds=600.0,
        max_altitude_ft=35000.0,
        max_ground_speed_kmh=800.0,
    )

    assert stats.total_flights == 1
    assert stats.per_aircraft == [aircraft_stats]
