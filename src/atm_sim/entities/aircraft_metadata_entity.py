""" """


# ============================================================================
# CLASS
# ============================================================================
class AircraftMetadataEntity:
    """ """

    def __init__(
        self,
        registration: str | None,
        manufacturer: str | None,
        model: str | None,
        typecode: str | None,
        operator: str | None,
    ) -> None:
        """ """
        self.registration: str | None = registration
        self.manufacturer: str | None = manufacturer
        self.model: str | None = model
        self.typecode: str | None = typecode
        self.operator: str | None = operator
