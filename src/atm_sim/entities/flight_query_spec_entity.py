""" """


# ============================================================================
# CLASS
# ============================================================================
class FlightQuerySpecEntity:
    """ """

    def __init__(
        self,
        airport: str | None = None,
        departure_airport: str | None = None,
        arrival_airport: str | None = None,
        callsign: str | None = None,
        icao24: str | None = None,
    ) -> None:
        """ """
        self.airport: str | None = airport
        self.departure_airport: str | None = departure_airport
        self.arrival_airport: str | None = arrival_airport
        self.callsign: str | None = callsign
        self.icao24: str | None = icao24
