""" """

# ============================================================================
# IMPORT
# ============================================================================
from datetime import datetime


# ============================================================================
# CLASS
# ============================================================================
class InvalidSimulationPeriodError(ValueError):
    """ """

    def __init__(
        self,
        begin: datetime,
        end: datetime,
    ) -> None:
        """ """
        super().__init__(f"start ({begin}) must be before end ({end})")


class MultipleSelectionModesError(ValueError):
    """ """

    def __init__(self) -> None:
        """ """
        super().__init__("Only one selection mode allowed: --airport, --origin/--destination, --callsign, or --icao24")
