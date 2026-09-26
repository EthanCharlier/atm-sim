""" """

# ============================================================================
# IMPORT
# ============================================================================

# ENTITIES IMPORT
from atm_sim.entities.aircraft_statistics_entity import AircraftStatisticsEntity


# ============================================================================
# CLASS
# ============================================================================
class SimulationStatisticsEntity:
    """ """

    def __init__(
        self,
        per_aircraft: list[AircraftStatisticsEntity],
        total_flights: int,
        average_duration_seconds: float,
        max_altitude_ft: float,
        max_ground_speed_kmh: float,
    ) -> None:
        """ """
        self.per_aircraft: list[AircraftStatisticsEntity] = per_aircraft
        self.total_flights: int = total_flights
        self.average_duration_seconds: float = average_duration_seconds
        self.max_altitude_ft: float = max_altitude_ft
        self.max_ground_speed_kmh: float = max_ground_speed_kmh
