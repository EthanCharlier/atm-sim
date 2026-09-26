""" """

# ============================================================================
# IMPORT
# ============================================================================
import time
from datetime import UTC, datetime, timedelta

# CONSTANTS IMPORT
from atm_sim.constants.constants import (
    DEFAULT_AIRPORT,
    DEFAULT_MAX_FLIGHTS,
    DEFAULT_SPEED_INDEX,
    DEFAULT_TICK_SECONDS,
    IDLE_SLEEP_SECONDS,
    MIN_RENDER_INTERVAL_SECONDS,
    PAUSE_KEY,
    QUIT_KEY,
    ENTER_KEY,
    SPEED_DOWN_KEY,
    SPEED_UP_KEY,
)

# ENTITIES IMPORT
from atm_sim.entities.aircraft_entity import AircraftEntity
from atm_sim.entities.clock_entity import SimClockEntity, resolve_speed_index
from atm_sim.entities.simulation_engine_entity import SimulationEngineEntity
from atm_sim.entities.aircraft_statistics_entity import AircraftStatisticsEntity
from atm_sim.entities.simulation_statistics_entity import SimulationStatisticsEntity

# ENUMS IMPORT
from atm_sim.enums.simulation_status_enum import SimulationStatusEnum

# EXEPTIONS IMPORT
from atm_sim.exceptions.exceptions import InvalidSimulationPeriodError, MultipleSelectionModesError

# SERVICES IMPORT
from atm_sim.services.airport_service import AirportService
from atm_sim.services.console_renderer_service import ConsoleRendererService
from atm_sim.services.keyboard_listener_service import KeyboardListenerService
from atm_sim.services.opensky_service import OpenSkyService


# ============================================================================
# CLASS
# ============================================================================
class SimulationService:
    """ """

    def __init__(
        self,
        opensky_service: OpenSkyService,
        airport_service: AirportService,
    ) -> None:
        """ """
        self.opensky_service: OpenSkyService = opensky_service
        self.airport_service: AirportService = airport_service

    def start(
        self,
        airports: list[str] | None = None,
        origins: list[str] | None = None,
        destinations: list[str] | None = None,
        callsigns: list[str] | None = None,
        icao24s: list[str] | None = None,
        airlines: list[str] | None = None,
        min_altitude_ft: float | None = None,
        max_altitude_ft: float | None = None,
        min_ground_speed_kmh: float | None = None,
        min_duration_seconds: float | None = None,
        begin: datetime | None = None,
        end: datetime | None = None,
        max_flights: int | None = None,
        tick_seconds: float | None = None,
        speed_factor: float | None = None,
    ) -> None:
        """ """
        self._validate_selection_mode(airports, origins, destinations, callsigns, icao24s)

        resolved_max_flights = max_flights if max_flights is not None else DEFAULT_MAX_FLIGHTS
        resolved_tick_seconds = tick_seconds if tick_seconds is not None else DEFAULT_TICK_SECONDS
        resolved_speed_index = resolve_speed_index(speed_factor) if speed_factor is not None else DEFAULT_SPEED_INDEX

        resolved_airports = airports
        if not resolved_airports and not origins and not destinations and not callsigns and not icao24s:
            resolved_airports = [DEFAULT_AIRPORT]

        if begin is None or end is None:
            resolved_begin, resolved_end = self._compute_yesterday_utc_range()
        else:
            resolved_begin, resolved_end = begin, end

        if resolved_begin >= resolved_end:
            raise InvalidSimulationPeriodError(resolved_begin, resolved_end)

        selection_label = self._format_selection_label(
            resolved_airports,
            origins,
            destinations,
            callsigns,
            icao24s,
        )

        print(f"Fetching {selection_label} between {resolved_begin} and {resolved_end}...")
        fleet = self.opensky_service.import_fleet_for_period(
            begin=resolved_begin,
            end=resolved_end,
            max_flights=resolved_max_flights,
            airports=resolved_airports,
            origins=origins,
            destinations=destinations,
            callsigns=callsigns,
            icao24s=icao24s,
            airlines=airlines,
            min_altitude_ft=min_altitude_ft,
            max_altitude_ft=max_altitude_ft,
            min_ground_speed_kmh=min_ground_speed_kmh,
            min_duration_seconds=min_duration_seconds,
        )
        print(f"Imported {len(fleet)} aircraft.")

        if not fleet:
            print("No aircraft to simulate, exiting.")
            return

        self._run(
            fleet=fleet,
            airport_label=selection_label,
            begin=resolved_begin,
            end=resolved_end,
            tick_seconds=resolved_tick_seconds,
            speed_index=resolved_speed_index,
        )

    @staticmethod
    def _validate_selection_mode(
        airports: list[str] | None,
        origins: list[str] | None,
        destinations: list[str] | None,
        callsigns: list[str] | None,
        icao24s: list[str] | None,
    ) -> None:
        """ """
        modes_used = sum(
            [
                bool(airports),
                bool(origins or destinations),
                bool(callsigns),
                bool(icao24s),
            ],
        )

        if modes_used > 1:
            raise MultipleSelectionModesError

    def _format_selection_label(
        self,
        airports: list[str] | None,
        origins: list[str] | None,
        destinations: list[str] | None,
        callsigns: list[str] | None,
        icao24s: list[str] | None,
    ) -> str:
        """ """
        if airports:
            names = [self._airport_display_name(code) for code in airports]
            return " / ".join(names)

        if origins and destinations:
            routes = [
                f"{self._airport_display_name(o)} -> {self._airport_display_name(d)}"
                for o in origins
                for d in destinations
            ]
            return ", ".join(routes)

        if origins:
            names = [self._airport_display_name(code) for code in origins]
            return f"departures from {' / '.join(names)}"

        if destinations:
            names = [self._airport_display_name(code) for code in destinations]
            return f"arrivals to {' / '.join(names)}"

        if callsigns:
            return f"callsign(s) {' / '.join(callsigns)}"

        if icao24s:
            return f"aircraft {' / '.join(icao24s)}"

        return DEFAULT_AIRPORT

    def _airport_display_name(
        self,
        code: str,
    ) -> str:
        """ """
        airport_info = self.airport_service.get_airport(code)
        if airport_info is None:
            return code
        return f"{airport_info.name} ({airport_info.icao})"

    @staticmethod
    def _run(
        fleet: list[AircraftEntity],
        airport_label: str,
        begin: datetime,
        end: datetime,
        tick_seconds: float,
        speed_index: int,
    ) -> None:
        """ """
        total_duration_seconds = (end - begin).total_seconds()

        clock = SimClockEntity(tick_seconds=tick_seconds, speed_index=speed_index)
        engine = SimulationEngineEntity(clock=clock)

        for aircraft in fleet:
            engine.add_aircraft(aircraft)

        listener = KeyboardListenerService()
        listener.start()

        ConsoleRendererService.reserve_space(len(fleet))

        last_render_time = 0.0

        try:
            while True:
                key = listener.read_key_nonblocking()

                if key == QUIT_KEY:
                    break

                SimulationService._handle_key_input(key, engine)

                status = SimulationService._advance_and_get_status(engine, total_duration_seconds)

                last_render_time = SimulationService._maybe_render(
                    engine=engine,
                    airport_label=airport_label,
                    begin=begin,
                    status=status,
                    last_render_time=last_render_time,
                )

                if status == SimulationStatusEnum.COMPLETE:
                    break

                SimulationService._sleep_for_status(status, engine)
        finally:
            listener.stop()

        print("\nPress [ESC] to quit or [ENTER] to see the simulation summary...")

        listener.start()
        try:
            show_summary = SimulationService._wait_for_summary_choice(listener)
        finally:
            listener.stop()

        if show_summary:
            statistics = SimulationService._compute_statistics(fleet, engine.clock.sim_time_elapsed)
            ConsoleRendererService.render_summary(airport_label, begin, end, statistics)

        print("\nSimulation stopped.")

    @staticmethod
    def _wait_for_summary_choice(
        listener: KeyboardListenerService,
    ) -> bool:
        """ """
        if not listener.is_interactive():
            return True

        while True:
            key = listener.read_key_nonblocking()

            if key == QUIT_KEY:
                return False
            if key == ENTER_KEY:
                return True

            time.sleep(IDLE_SLEEP_SECONDS)

    @staticmethod
    def _compute_statistics(
        fleet: list[AircraftEntity],
        final_elapsed_seconds: float,
    ) -> SimulationStatisticsEntity:
        """ """
        per_aircraft = [
            AircraftStatisticsEntity(
                callsign=aircraft.callsign,
                origin_icao=aircraft.origin_airport.icao,
                destination_icao=aircraft.destination_airport.icao,
                type_code=aircraft.metadata.typecode if aircraft.metadata and aircraft.metadata.typecode else "?",
                status=aircraft.status,
                progress_percent=aircraft.get_progress_percent(final_elapsed_seconds),
                elapsed_seconds=max(
                    0.0,
                    min(final_elapsed_seconds, aircraft.trajectory.end_time_seconds)
                    - aircraft.trajectory.start_time_seconds,
                ),
                max_altitude_ft=aircraft.trajectory.get_max_altitude_ft_until(final_elapsed_seconds),
                max_ground_speed_kmh=aircraft.trajectory.get_max_ground_speed_kmh_until(final_elapsed_seconds),
            )
            for aircraft in fleet
        ]

        total_flights = len(per_aircraft)

        if total_flights == 0:
            return SimulationStatisticsEntity(
                per_aircraft=[],
                total_flights=0,
                average_duration_seconds=0.0,
                max_altitude_ft=0.0,
                max_ground_speed_kmh=0.0,
            )

        return SimulationStatisticsEntity(
            per_aircraft=per_aircraft,
            total_flights=total_flights,
            average_duration_seconds=sum(a.elapsed_seconds for a in per_aircraft) / total_flights,
            max_altitude_ft=max(a.max_altitude_ft for a in per_aircraft),
            max_ground_speed_kmh=max(a.max_ground_speed_kmh for a in per_aircraft),
        )

    @staticmethod
    def _handle_key_input(
        key: str | None,
        engine: SimulationEngineEntity,
    ) -> None:
        """ """
        if key == PAUSE_KEY:
            if engine.clock.is_paused():
                engine.clock.resume()
            else:
                engine.clock.pause()
        elif key == SPEED_UP_KEY:
            engine.clock.increase_speed()
        elif key == SPEED_DOWN_KEY:
            engine.clock.decrease_speed()

    @staticmethod
    def _advance_and_get_status(
        engine: SimulationEngineEntity,
        total_duration_seconds: float,
    ) -> SimulationStatusEnum:
        """ """
        status = engine.get_status(total_duration_seconds)

        if status == SimulationStatusEnum.RUNNING:
            engine.tick()
            status = engine.get_status(total_duration_seconds)

        return status

    @staticmethod
    def _maybe_render(
        engine: SimulationEngineEntity,
        airport_label: str,
        begin: datetime,
        status: SimulationStatusEnum,
        last_render_time: float,
    ) -> float:
        """ """
        now = time.monotonic()
        should_render = (
            status == SimulationStatusEnum.COMPLETE or (now - last_render_time) >= MIN_RENDER_INTERVAL_SECONDS
        )

        if not should_render:
            return last_render_time

        ConsoleRendererService.render(engine, airport_label, begin, status)
        return now

    @staticmethod
    def _sleep_for_status(
        status: SimulationStatusEnum,
        engine: SimulationEngineEntity,
    ) -> None:
        """ """
        if status == SimulationStatusEnum.RUNNING:
            time.sleep(engine.clock.tick_seconds / abs(engine.clock.speed_factor))
        else:
            time.sleep(IDLE_SLEEP_SECONDS)

    @staticmethod
    def _compute_yesterday_utc_range() -> tuple[datetime, datetime]:
        """ """
        now_utc = datetime.now(UTC)
        today_midnight = datetime(
            now_utc.year,
            now_utc.month,
            now_utc.day,
            tzinfo=UTC,
        )
        yesterday_start = today_midnight - timedelta(days=1)
        yesterday_end = today_midnight

        return yesterday_start, yesterday_end
