""" """

# ============================================================================
# IMPORT
# ============================================================================
import logging

import airportsdata

# ENTITIES IMPORT
from atm_sim.entities.airport_entity import AirportEntity

# ============================================================================
# LOGGER
# ============================================================================
logger = logging.getLogger(__name__)


# ============================================================================
# CLASS
# ============================================================================
class AirportService:
    """ """

    def __init__(self) -> None:
        """ """
        self._airports_by_icao = airportsdata.load("ICAO")
        logger.info("Loaded %d airports from airportsdata", len(self._airports_by_icao))

    def get_airport(
        self,
        icao: str,
    ) -> AirportEntity | None:
        """ """
        data = self._airports_by_icao.get(icao.upper())

        if data is None:
            logger.warning("Unknown airport ICAO code: %s", icao)
            return None

        return AirportEntity(
            icao=data["icao"],
            iata=data["iata"],
            name=data["name"],
            city=data["city"],
            country=data["country"],
            lat=float(data["lat"]),
            lon=float(data["lon"]),
            elevation_ft=float(data["elevation"]),
            timezone=data["tz"],
        )
