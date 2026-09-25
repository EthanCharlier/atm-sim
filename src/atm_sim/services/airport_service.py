"""
"""

# ============================================================================
# IMPORT
# ============================================================================
import airportsdata

# ENTITIES IMPORT
from atm_sim.entities.airport_entity import AirportEntity


# ============================================================================
# CLASS
# ============================================================================
class AirportService:
    """
    """

    def __init__(self) -> None:
        """
        """
        self._airports_by_icao: dict = airportsdata.load("ICAO")

    def get_airport(
            self,
            icao: str,
    ) -> AirportEntity | None:
        """
        """
        data = self._airports_by_icao.get(icao.upper())

        if data is None:
            return None

        return AirportEntity(
            icao = data["icao"],
            iata = data["iata"],
            name = data["name"],
            city = data["city"],
            country = data["country"],
            lat = float(data["lat"]),
            lon = float(data["lon"]),
            elevation_ft = float(data["elevation"]),
            timezone = data["tz"],
        )
