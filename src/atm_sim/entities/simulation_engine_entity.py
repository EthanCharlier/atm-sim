""" """

# ============================================================================
# IMPORT
# ============================================================================

# ENTITIES IMPORT
from atm_sim.entities.aircraft_entity import AircraftEntity
from atm_sim.entities.clock_entity import SimClockEntity

# ENUMS IMPORTS
from atm_sim.enums.simulation_status_enum import SimulationStatusEnum


# ============================================================================
# CLASS
# ============================================================================
class SimulationEngineEntity:
    """ """

    def __init__(
        self,
        clock: SimClockEntity,
    ) -> None:
        """ """
        self.clock: SimClockEntity = clock
        self.fleet: list[AircraftEntity] = []

    def add_aircraft(
        self,
        aircraft: AircraftEntity,
    ) -> None:
        """ """
        self.fleet.append(aircraft)

    def tick(self) -> None:
        """ """
        self.clock.advance()
        for aircraft in self.fleet:
            aircraft.update(self.clock.sim_time_elapsed)

    def get_status(
        self,
        total_duration_seconds: float,
    ) -> SimulationStatusEnum:
        """ """
        is_complete = self.clock.sim_time_elapsed >= total_duration_seconds
        return self.clock.get_status(is_complete=is_complete)
