"""
"""

# ============================================================================
# IMPORT
# ============================================================================
import bisect

# SERVICES IMPORT
from atm_sim.services.navigation_service import NavigationService

# ENTITIES IMPORT
from atm_sim.entities.trajectory_point_entity import TrajectoryPointEntity


# ============================================================================
# CLASS
# ============================================================================
class TrajectoryEntity:
    """
    """

    def __init__(
        self,
        points: list[TrajectoryPointEntity],
    ) -> None:
        """
        """
        if len(points) < 2:
            raise ValueError("TrajectoryEntity requires at least 2 points")

        self.points: list[TrajectoryPointEntity] = points
        self.start_time_seconds: float = points[0].time_offset_seconds
        self.end_time_seconds: float = points[-1].time_offset_seconds

        self._time_offsets: list[float] = [point.time_offset_seconds for point in points]

    def has_started_at(
        self,
        global_elapsed_seconds: float,
    ) -> bool:
        """
        """
        return global_elapsed_seconds >= self.start_time_seconds

    def has_arrived_at(
        self,
        global_elapsed_seconds: float,
    ) -> bool:
        """
        """
        return global_elapsed_seconds >= self.end_time_seconds

    def get_first_point_state(self) -> tuple[float, float, float]:
        """
        """
        first_point = self.points[0]
        return first_point.lat, first_point.lon, first_point.altitude_ft

    def get_last_point_state(self) -> tuple[float, float, float]:
        """
        """
        last_point = self.points[-1]
        return last_point.lat, last_point.lon, last_point.altitude_ft

    def get_position_at(
        self,
        global_elapsed_seconds: float,
    ) -> tuple[float, float, float]:
        """
        """
        if global_elapsed_seconds <= self.start_time_seconds:
            return self.get_first_point_state()

        if global_elapsed_seconds >= self.end_time_seconds:
            return self.get_last_point_state()

        current_point, next_point, fraction = self._locate(global_elapsed_seconds)

        lat, lon = NavigationService.compute_intermediate_position(
            current_point.lat, current_point.lon,
            next_point.lat, next_point.lon,
            fraction,
        )
        altitude_ft = NavigationService.compute_intermediate_value(
            current_point.altitude_ft, next_point.altitude_ft, fraction
        )

        return lat, lon, altitude_ft

    def get_in_flight_state_at(
        self,
        global_elapsed_seconds: float,
    ) -> tuple[float, float, float, float, float]:
        """
        """
        clamped_seconds = self._clamp_to_range(global_elapsed_seconds)
        current_point, next_point, fraction = self._locate(clamped_seconds)

        lat, lon = NavigationService.compute_intermediate_position(
            current_point.lat, current_point.lon,
            next_point.lat, next_point.lon,
            fraction,
        )
        altitude_ft = NavigationService.compute_intermediate_value(
            current_point.altitude_ft, next_point.altitude_ft, fraction
        )
        ground_speed_kmh = NavigationService.compute_intermediate_value(
            current_point.ground_speed_kmh, next_point.ground_speed_kmh, fraction
        )
        vertical_rate_ft_per_min = NavigationService.compute_intermediate_value(
            current_point.vertical_rate_ft_per_min, next_point.vertical_rate_ft_per_min, fraction
        )

        return lat, lon, altitude_ft, ground_speed_kmh, vertical_rate_ft_per_min

    def get_max_altitude_ft(self) -> float:
        """
        """
        return max(point.altitude_ft for point in self.points)

    def get_max_ground_speed_kmh(self) -> float:
        """
        """
        return max(point.ground_speed_kmh for point in self.points)

    def get_duration_seconds(self) -> float:
        """
        """
        return self.end_time_seconds - self.start_time_seconds

    def _clamp_to_range(
        self,
        global_elapsed_seconds: float,
    ) -> float:
        """
        """
        return max(self.start_time_seconds, min(global_elapsed_seconds, self.end_time_seconds))

    def _locate(
        self,
        global_elapsed_seconds: float,
    ) -> tuple[TrajectoryPointEntity, TrajectoryPointEntity, float]:
        """
        """
        index = bisect.bisect_right(self._time_offsets, global_elapsed_seconds) - 1
        index = max(0, min(index, len(self.points) - 2))

        current_point = self.points[index]
        next_point = self.points[index + 1]
        segment_duration = next_point.time_offset_seconds - current_point.time_offset_seconds

        if segment_duration <= 0:
            return current_point, next_point, 0.0

        fraction = (global_elapsed_seconds - current_point.time_offset_seconds) / segment_duration
        return current_point, next_point, fraction
