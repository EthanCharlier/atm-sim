""" """


# ============================================================================
# CLASS
# ============================================================================
class TrajectoryPointEntity:
    """ """

    def __init__(
        self,
        time_offset_seconds: float,
        lat: float,
        lon: float,
        altitude_ft: float,
        ground_speed_kmh: float,
        vertical_rate_ft_per_min: float,
        on_ground: bool,
    ) -> None:
        """ """
        self.time_offset_seconds: float = time_offset_seconds
        self.lat: float = lat
        self.lon: float = lon
        self.altitude_ft: float = altitude_ft
        self.ground_speed_kmh: float = ground_speed_kmh
        self.vertical_rate_ft_per_min: float = vertical_rate_ft_per_min
        self.on_ground: bool = on_ground
