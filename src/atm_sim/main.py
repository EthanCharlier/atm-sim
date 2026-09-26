""" """

# ============================================================================
# IMPORT
# ============================================================================
import argparse
import logging
import sys
from datetime import UTC, datetime

from dotenv import load_dotenv
from pyopensky.trino import Trino

# CONSTANTS IMPORT
from atm_sim.constants.constants import LOG_FILE_PATH

# SERVICES IMPORT
from atm_sim.services.airport_service import AirportService
from atm_sim.services.opensky_service import OpenSkyService
from atm_sim.services.simulation_service import SimulationService
from atm_sim.services.aircraft_database_service import AircraftDatabaseService

# ============================================================================
# LOGGER
# ============================================================================
logger = logging.getLogger(__name__)


# ============================================================================
# FUNCTIONS
# ============================================================================
def parse_utc_datetime(
    value: str,
) -> datetime:
    """ """
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def parse_arguments() -> argparse.Namespace:
    """ """
    parser = argparse.ArgumentParser(description="ATM simulation from OpenSky historical data")
    parser.add_argument(
        "--start",
        type=parse_utc_datetime,
        default=None,
        help="Start of the period (ISO format, e.g. 2026-09-20T00:00:00). Defaults to yesterday midnight UTC.",
    )
    parser.add_argument(
        "--end",
        type=parse_utc_datetime,
        default=None,
        help="End of the period (ISO format, e.g. 2026-09-20T12:00:00). Defaults to today midnight UTC.",
    )
    parser.add_argument(
        "--airport",
        type=str,
        nargs="+",
        default=None,
        help="One or more ICAO airport codes, matching departure OR arrival (default: LFBO)",
    )
    parser.add_argument(
        "--origin",
        type=str,
        nargs="+",
        default=None,
        help="One or more ICAO departure airport codes",
    )
    parser.add_argument(
        "--destination",
        type=str,
        nargs="+",
        default=None,
        help="One or more ICAO arrival airport codes",
    )
    parser.add_argument(
        "--callsign",
        type=str,
        nargs="+",
        default=None,
        help="One or more callsigns to filter on",
    )
    parser.add_argument(
        "--icao24",
        type=str,
        nargs="+",
        default=None,
        help="One or more specific ICAO24 transponder addresses",
    )
    parser.add_argument(
        "--airline",
        type=str,
        nargs="+",
        default=None,
        help="Only keep flights whose callsign starts with one of these ICAO airline prefixes (e.g. AFR RYR)",
    )
    parser.add_argument(
        "--min-altitude",
        type=float,
        default=None,
        help="Only keep flights that reach at least this altitude (ft)",
    )
    parser.add_argument(
        "--max-altitude",
        type=float,
        default=None,
        help="Only keep flights that never exceed this altitude (ft)",
    )
    parser.add_argument(
        "--min-speed",
        type=float,
        default=None,
        help="Only keep flights that reach at least this ground speed (km/h)",
    )
    parser.add_argument(
        "--min-duration",
        type=float,
        default=None,
        help="Only keep flights lasting at least this long (seconds)",
    )
    parser.add_argument(
        "--max-flights",
        type=int,
        default=None,
        help="Maximum number of flights to import, distributed across the query specs (default: 5)",
    )
    parser.add_argument(
        "--tick-seconds",
        type=float,
        default=None,
        help="Simulated seconds advanced per tick (default: 1.0)",
    )
    parser.add_argument(
        "--speed-factor",
        type=float,
        default=None,
        help="Simulation speed, snapped to the nearest predefined level (default: 1.0)",
    )
    return parser.parse_args()


def _configure_logging() -> None:
    """ """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        filename=LOG_FILE_PATH,
        filemode="a",
    )


def main() -> None:
    """ """
    _configure_logging()

    # ---

    load_dotenv()
    args = parse_arguments()

    # ---

    try:
        trino = Trino()
        airport_service = AirportService()
        aircraft_database_service = AircraftDatabaseService()
        opensky_service = OpenSkyService(
            trino=trino,
            airport_service=airport_service,
            aircraft_database_service=aircraft_database_service,
        )
        simulation_service = SimulationService(
            opensky_service=opensky_service,
            airport_service=airport_service,
        )

        simulation_service.start(
            airports=args.airport,
            origins=args.origin,
            destinations=args.destination,
            callsigns=args.callsign,
            icao24s=args.icao24,
            airlines=args.airline,
            min_altitude_ft=args.min_altitude,
            max_altitude_ft=args.max_altitude,
            min_ground_speed_kmh=args.min_speed,
            min_duration_seconds=args.min_duration,
            begin=args.start,
            end=args.end,
            max_flights=args.max_flights,
            tick_seconds=args.tick_seconds,
            speed_factor=args.speed_factor,
        )
    except ValueError as error:
        print(f"Invalid input: {error}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(0)
    except Exception:
        logger.exception("Unexpected error")
        sys.exit(1)


if __name__ == "__main__":
    main()
