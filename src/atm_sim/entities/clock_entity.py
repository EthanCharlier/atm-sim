""" """

# ============================================================================
# IMPORT
# ============================================================================

# ENUMS IMPORT
# CONSTANTS IMPORT
from atm_sim.constants.constants import DEFAULT_SPEED_INDEX, SPEED_LEVELS
from atm_sim.enums.simulation_status_enum import SimulationStatusEnum


# ============================================================================
# FUNCTIONS
# ============================================================================
def resolve_speed_index(value: float) -> int:
    """ """
    target = int(value)
    return min(range(len(SPEED_LEVELS)), key=lambda i: abs(SPEED_LEVELS[i] - target))


# ============================================================================
# CLASS
# ============================================================================
class SimClockEntity:
    """ """

    def __init__(
        self,
        tick_seconds: float,
        speed_index: int = DEFAULT_SPEED_INDEX,
    ) -> None:
        """ """
        self.tick_seconds: float = tick_seconds
        self._speed_index: int = speed_index

        self.sim_time_elapsed: float = 0.0
        self._paused: bool = False

    @property
    def speed_factor(self) -> float:
        """ """
        return SPEED_LEVELS[self._speed_index]

    def advance(self) -> None:
        """ """
        if self._paused:
            return

        direction = 1.0 if self.speed_factor > 0 else -1.0
        self.sim_time_elapsed = max(0.0, self.sim_time_elapsed + self.tick_seconds * direction)

    def pause(self) -> None:
        """ """
        self._paused = True

    def resume(self) -> None:
        """ """
        self._paused = False

    def is_paused(self) -> bool:
        """ """
        return self._paused

    def increase_speed(self) -> None:
        """ """
        self._speed_index = min(self._speed_index + 1, len(SPEED_LEVELS) - 1)

    def decrease_speed(self) -> None:
        """ """
        self._speed_index = max(self._speed_index - 1, 0)

    def get_status(
        self,
        is_complete: bool,
    ) -> SimulationStatusEnum:
        """ """
        if is_complete:
            return SimulationStatusEnum.COMPLETE
        if self._paused:
            return SimulationStatusEnum.PAUSED
        return SimulationStatusEnum.RUNNING
