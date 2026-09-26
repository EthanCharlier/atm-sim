""" """

# ============================================================================
# IMPORT
# ============================================================================

# ENTITIES IMPORT
from atm_sim.entities.airport_entity import AirportEntity
from atm_sim.entities.trajectory_entity import TrajectoryEntity
from atm_sim.entities.aircraft_metadata_entity import AircraftMetadataEntity

# ENUMS IMPORTS
from atm_sim.enums.aircraft_status_enum import AircraftStatusEnum


# ============================================================================
# CLASS
# ============================================================================
class AircraftEntity:
    """ """

    def __init__(
        self,
        callsign: str,
        origin_airport: AirportEntity,
        destination_airport: AirportEntity,
        trajectory: TrajectoryEntity,
        metadata: AircraftMetadataEntity | None = None,
    ) -> None:
        """ """
        self.callsign: str = callsign
        self.origin_airport: AirportEntity = origin_airport
        self.destination_airport: AirportEntity = destination_airport
        self.trajectory: TrajectoryEntity = trajectory
        self.metadata: AircraftMetadataEntity | None = metadata

        self.current_lat: float
        self.current_lon: float
        self.current_altitude_ft: float
        self.current_ground_speed_kmh: float
        self.current_vertical_rate_ft_per_min: float
        self.has_started: bool = False
        self.arrived: bool = False
        self.status: AircraftStatusEnum = AircraftStatusEnum.WAITING

        self._initialized: bool = False

        self.update(0.0)

    def update(
        self,
        global_elapsed_seconds: float,
    ) -> None:
        """ """
        if self._initialized:
            still_waiting = (not self.has_started) and global_elapsed_seconds <= self.trajectory.start_time_seconds
            still_arrived = self.arrived and global_elapsed_seconds >= self.trajectory.end_time_seconds

            if still_waiting or still_arrived:
                return

        self.has_started = self.trajectory.has_started_at(global_elapsed_seconds)
        arrived_now = self.trajectory.has_arrived_at(global_elapsed_seconds)

        if not self.has_started:
            self.current_lat, self.current_lon, self.current_altitude_ft = self.trajectory.get_first_point_state()
            self.current_ground_speed_kmh = 0.0
            self.current_vertical_rate_ft_per_min = 0.0
        elif arrived_now:
            self.current_lat, self.current_lon, self.current_altitude_ft = self.trajectory.get_last_point_state()
            self.current_ground_speed_kmh = 0.0
            self.current_vertical_rate_ft_per_min = 0.0
        else:
            (
                self.current_lat,
                self.current_lon,
                self.current_altitude_ft,
                self.current_ground_speed_kmh,
                self.current_vertical_rate_ft_per_min,
            ) = self.trajectory.get_in_flight_state_at(global_elapsed_seconds)

        self.arrived = arrived_now
        self.status = self._compute_status()
        self._initialized = True

    def get_progress_percent(
        self,
        global_elapsed_seconds: float,
    ) -> float:
        """ """
        if self.status == AircraftStatusEnum.WAITING:
            return 0.0
        if self.status == AircraftStatusEnum.ARRIVED:
            return 100.0

        duration = self.trajectory.end_time_seconds - self.trajectory.start_time_seconds
        if duration <= 0:
            return 0.0

        elapsed = global_elapsed_seconds - self.trajectory.start_time_seconds
        return elapsed / duration * 100

    def _compute_status(self) -> AircraftStatusEnum:
        """ """
        if not self.has_started:
            return AircraftStatusEnum.WAITING
        if self.arrived:
            return AircraftStatusEnum.ARRIVED
        return AircraftStatusEnum.IN_FLIGHT
