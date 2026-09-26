""" """

# ============================================================================
# IMPORT
# ============================================================================

# ENUMS IMPORT
from atm_sim.enums.aircraft_status_enum import AircraftStatusEnum


# ============================================================================
# CLASS
# ============================================================================
class AircraftStatisticsEntity:
    """ """

    def __init__(
        self,
        callsign: str,
        origin_icao: str,
        destination_icao: str,
        type_code: str,
        status: AircraftStatusEnum,
        progress_percent: float,
        elapsed_seconds: float,
        max_altitude_ft: float,
        max_ground_speed_kmh: float,
    ) -> None:
        """ """
        self.callsign: str = callsign
        self.origin_icao: str = origin_icao
        self.destination_icao: str = destination_icao
        self.type_code: str = type_code
        self.status: AircraftStatusEnum = status
        self.progress_percent: float = progress_percent
        self.elapsed_seconds: float = elapsed_seconds
        self.max_altitude_ft: float = max_altitude_ft
        self.max_ground_speed_kmh: float = max_ground_speed_kmh
