""" """

# ============================================================================
# IMPORT
# ============================================================================
import math

# CONSTANTS IMPORT
from atm_sim.constants.constants import EARTH_RADIUS_METERS


# ============================================================================
# CLASS
# ============================================================================
class NavigationService:
    """ """

    @staticmethod
    def compute_distance_meters(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """ """
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return EARTH_RADIUS_METERS * c

    @staticmethod
    def compute_intermediate_position(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        fraction: float,
    ) -> tuple[float, float]:
        """ """
        clamped_fraction = max(0.0, min(1.0, fraction))

        lat = lat1 + (lat2 - lat1) * clamped_fraction
        lon = lon1 + (lon2 - lon1) * clamped_fraction

        return lat, lon

    @staticmethod
    def compute_intermediate_value(
        value1: float,
        value2: float,
        fraction: float,
    ) -> float:
        """ """
        clamped_fraction = max(0.0, min(1.0, fraction))

        return value1 + (value2 - value1) * clamped_fraction
