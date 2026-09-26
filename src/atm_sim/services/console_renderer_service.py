""" """

# ============================================================================
# IMPORT
# ============================================================================
from datetime import datetime, timedelta

# CONSTANTS IMPORT
from atm_sim.constants.constants import (
    CLEAR_LINE,
    COLOR_ARRIVED,
    COLOR_IN_FLIGHT,
    COLOR_RESET,
    COLOR_WAITING,
    CURSOR_HOME,
    STATUS_COLORS,
    STATUS_SORT_ORDER,
)

# ENTITIES IMPORT
from atm_sim.entities.simulation_engine_entity import SimulationEngineEntity

# ENUMS IMPORT
from atm_sim.enums.aircraft_status_enum import AircraftStatusEnum
from atm_sim.enums.simulation_status_enum import SimulationStatusEnum


# ============================================================================
# CLASS
# ============================================================================
class ConsoleRendererService:
    """ """

    @staticmethod
    def reserve_space(
        fleet_size: int,
    ) -> None:
        """ """
        print("\n" * (fleet_size + 7))

    @staticmethod
    def render(
        engine: SimulationEngineEntity,
        airport_label: str,
        begin: datetime,
        status: SimulationStatusEnum,
    ) -> None:
        """ """
        current_utc = begin + timedelta(seconds=engine.clock.sim_time_elapsed)

        counts: dict[AircraftStatusEnum, int] = {
            AircraftStatusEnum.WAITING: 0,
            AircraftStatusEnum.IN_FLIGHT: 0,
            AircraftStatusEnum.ARRIVED: 0,
        }

        for aircraft in engine.fleet:
            counts[aircraft.status] += 1

        sorted_fleet = sorted(
            engine.fleet,
            key=lambda a: (
                STATUS_SORT_ORDER[a.status],
                -a.get_progress_percent(engine.clock.sim_time_elapsed),
            ),
        )

        lines: list[str] = [
            f"OpenSky ATM Simulation — {airport_label}  |  speed x{engine.clock.speed_factor:g}  |  [{status.value}]",
            f"Simulated time: {current_utc:%Y-%m-%d %H:%M:%S} UTC  (t+{engine.clock.sim_time_elapsed:.0f}s)",
            f"{COLOR_IN_FLIGHT}{counts[AircraftStatusEnum.IN_FLIGHT]} in flight{COLOR_RESET}  |  "
            f"{COLOR_WAITING}{counts[AircraftStatusEnum.WAITING]} waiting{COLOR_RESET}  |  "
            f"{COLOR_ARRIVED}{counts[AircraftStatusEnum.ARRIVED]} arrived{COLOR_RESET}  |  "
            f"controls: [SPACE] pause  [+/-] speed  [ESC] quit",
            "",
            f"{'CALLSIGN':<10} {'ORIGIN':<7} {'DEST':<7} {'STATUS':<11} {'PROGRESS':>8} {'LAT':>9} {'LON':>10} "
            f"{'ALT (ft)':>9} {'SPEED (km/h)':>13} {'VRATE (ft/min)':>15}",
            "-" * 110,
        ]

        for aircraft in sorted_fleet:
            color = STATUS_COLORS[aircraft.status]
            progress = aircraft.get_progress_percent(engine.clock.sim_time_elapsed)

            lines.append(
                f"{aircraft.callsign:<10} {aircraft.origin_airport.icao:<7} {aircraft.destination_airport.icao:<7} "
                f"{color}{aircraft.status.value:<11}{COLOR_RESET} {progress:>7.1f}% "
                f"{aircraft.current_lat:>9.4f} {aircraft.current_lon:>10.4f} "
                f"{aircraft.current_altitude_ft:>9.0f} "
                f"{aircraft.current_ground_speed_kmh:>13.0f} "
                f"{aircraft.current_vertical_rate_ft_per_min:>+15.0f}",
            )

        output = CURSOR_HOME + "\n".join(f"{line}{CLEAR_LINE}" for line in lines)
        print(output)
