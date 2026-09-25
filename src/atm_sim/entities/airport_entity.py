"""
"""

# ============================================================================
# CLASS
# ============================================================================
class AirportEntity:
    """
    """

    def __init__(
        self,
        icao: str,
        iata: str,
        name: str,
        city: str,
        country: str,
        lat: float,
        lon: float,
        elevation_ft: float,
        timezone: str,
    ) -> None:
        """
        """
        self.icao: str = icao
        self.iata: str = iata
        self.name: str = name
        self.city: str = city
        self.country: str = country
        self.lat: float = lat
        self.lon: float = lon
        self.elevation_ft: float = elevation_ft
        self.timezone: str = timezone

    @staticmethod
    def unknown() -> "AirportEntity":
        """
        """
        return AirportEntity(
            icao = "????",
            iata = "",
            name = "Unknown airport",
            city = "",
            country = "",
            lat = 0.0,
            lon = 0.0,
            elevation_ft = 0.0,
            timezone = ""
        )
