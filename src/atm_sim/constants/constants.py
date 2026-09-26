""" """

# ============================================================================
# IMPORT
# ============================================================================
from pathlib import Path

# ENUMS IMPORTS
from atm_sim.enums.aircraft_status_enum import AircraftStatusEnum

# ============================================================================
# CONSTANTS
# ============================================================================

# ----------------------------------------------------------------------------
# SIMULATION
# ----------------------------------------------------------------------------
EARTH_RADIUS_METERS: float = 6371000.0
METERS_PER_FOOT: float = 0.3048
MS_TO_KMH: float = 3.6
MS_TO_FT_PER_MIN: float = 196.8504
SPEED_LEVELS: list[float] = [-3600.0, -60.0, -5.0, 1.0, 5.0, 60.0, 3600.0]
MIN_TRAJECTORY_POINTS: int = 2

# ----------------------------------------------------------------------------
# DEFAULT VALUE
# ----------------------------------------------------------------------------
DEFAULT_AIRPORT: str = "LFBO"
DEFAULT_MAX_FLIGHTS: int = 5
DEFAULT_TICK_SECONDS: float = 1.0
DEFAULT_SPEED_INDEX: int = 3

# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
CURSOR_HOME: str = "\033[H"
CLEAR_LINE: str = "\033[K"
COLOR_RESET: str = "\033[0m"
COLOR_WAITING: str = "\033[33m"
COLOR_IN_FLIGHT: str = "\033[36m"
COLOR_ARRIVED: str = "\033[32m"
STATUS_SORT_ORDER: dict[AircraftStatusEnum, int] = {
    AircraftStatusEnum.IN_FLIGHT: 0,
    AircraftStatusEnum.WAITING: 1,
    AircraftStatusEnum.ARRIVED: 2,
}
STATUS_COLORS: dict[AircraftStatusEnum, str] = {
    AircraftStatusEnum.WAITING: COLOR_WAITING,
    AircraftStatusEnum.IN_FLIGHT: COLOR_IN_FLIGHT,
    AircraftStatusEnum.ARRIVED: COLOR_ARRIVED,
}
MIN_RENDER_INTERVAL_SECONDS: float = 0.05
IDLE_SLEEP_SECONDS: float = 0.1
PAUSE_KEY: str = " "
QUIT_KEY: str = "\x1b"
SPEED_UP_KEY: str = "+"
SPEED_DOWN_KEY: str = "-"

# ----------------------------------------------------------------------------
# LOG
# ----------------------------------------------------------------------------
LOG_FILE_PATH = Path("atm-sim.log")

# ----------------------------------------------------------------------------
# AIRCRAFT DATABASE
# ----------------------------------------------------------------------------
AIRCRAFT_DATABASE_URL: str = "https://opensky-network.org/datasets/metadata/aircraftDatabase.csv"
AIRCRAFT_DATABASE_CACHE_PATH: Path = Path.home() / ".cache" / "atm-sim" / "aircraftDatabase.csv"
