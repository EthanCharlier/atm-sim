""" """

# ============================================================================
# IMPORT
# ============================================================================
import logging
import urllib.error
import urllib.request

import pandas as pd

# CONSTANTS IMPORT
from atm_sim.constants.constants import AIRCRAFT_DATABASE_CACHE_PATH, AIRCRAFT_DATABASE_URL

# ENTITIES IMPORT
from atm_sim.entities.aircraft_metadata_entity import AircraftMetadataEntity

# EXCEPTIONS IMPORT
from atm_sim.exceptions.exceptions import AircraftDatabaseDownloadError

# ============================================================================
# LOGGER
# ============================================================================
logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================
_DATABASE_COLUMNS: list[str] = ["icao24", "registration", "manufacturername", "model", "typecode", "operator"]


# ============================================================================
# CLASS
# ============================================================================
class AircraftDatabaseService:
    """ """

    def __init__(self) -> None:
        """ """
        self._ensure_cached()
        self._aircraft_by_icao24: dict[str, dict[str, str]] = self._load_database()

    def get_aircraft(
        self,
        icao24: str,
    ) -> AircraftMetadataEntity | None:
        """ """
        data = self._aircraft_by_icao24.get(icao24.lower())

        if data is None:
            return None

        return AircraftMetadataEntity(
            registration=data["registration"] or None,
            manufacturer=data["manufacturername"] or None,
            model=data["model"] or None,
            typecode=data["typecode"] or None,
            operator=data["operator"] or None,
        )

    @staticmethod
    def _ensure_cached() -> None:
        """ """
        if AIRCRAFT_DATABASE_CACHE_PATH.exists():
            logger.info("Aircraft database already cached at %s", AIRCRAFT_DATABASE_CACHE_PATH)
            return

        logger.info("Downloading aircraft database from %s", AIRCRAFT_DATABASE_URL)

        AIRCRAFT_DATABASE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

        try:
            urllib.request.urlretrieve(AIRCRAFT_DATABASE_URL, AIRCRAFT_DATABASE_CACHE_PATH)  # noqa: S310 -- fixed internal URL constant, not user input
        except (urllib.error.URLError, OSError) as error:
            logger.exception("Failed to download aircraft database from %s", AIRCRAFT_DATABASE_URL)
            raise AircraftDatabaseDownloadError(AIRCRAFT_DATABASE_URL) from error

        logger.info("Aircraft database downloaded to %s", AIRCRAFT_DATABASE_CACHE_PATH)

    @staticmethod
    def _load_database() -> dict[str, dict[str, str]]:
        """ """
        logger.info("Loading aircraft database from %s", AIRCRAFT_DATABASE_CACHE_PATH)

        database_df = pd.read_csv(
            AIRCRAFT_DATABASE_CACHE_PATH,
            usecols=_DATABASE_COLUMNS,
            dtype=str,
            keep_default_na=False,
        )
        database_df["icao24"] = database_df["icao24"].str.lower()
        database_df = database_df.drop_duplicates(subset="icao24", keep="first")

        raw = database_df.set_index("icao24").to_dict(orient="index")
        result = {str(icao24): {str(key): str(value) for key, value in row.items()} for icao24, row in raw.items()}

        logger.info("Loaded %d aircraft records", len(result))

        return result
