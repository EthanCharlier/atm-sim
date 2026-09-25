"""
"""

# ============================================================================
# IMPORT
# ============================================================================
import random
import logging
import pandas as pd
from typing import cast
from datetime import datetime
from pyopensky.trino import Trino
from trino.exceptions import Error as TrinoError

# ENTITIES IMPORT
from atm_sim.entities.airport_entity import AirportEntity
from atm_sim.entities.aircraft_entity import AircraftEntity
from atm_sim.entities.trajectory_entity import TrajectoryEntity
from atm_sim.entities.trajectory_point_entity import TrajectoryPointEntity

# SERVICES IMPORT
from atm_sim.services.airport_service import AirportService

# CONSTANTS IMPORT
from atm_sim.constants.constants import (
    METERS_PER_FOOT,
    MS_TO_KMH,
    MS_TO_FT_PER_MIN
)


# ============================================================================
# LOGGER
# ===========================================================================
logger = logging.getLogger(__name__)


# ============================================================================
# FUNCTIONS
# ============================================================================
def _to_unix_seconds(
    value: pd.Timestamp | int | float,
) -> float:
    """
    """
    if isinstance(value, pd.Timestamp):
        return value.timestamp()
    return float(value)


def _distribute_quotas(
    num_specs: int,
    max_flights: int,
) -> list[int]:
    """
    """
    base = max_flights // num_specs
    remainder = max_flights % num_specs

    quotas = [base] * num_specs

    if remainder > 0:
        bonus_indices = random.sample(range(num_specs), remainder)
        for index in bonus_indices:
            quotas[index] += 1

    return quotas


def _build_query_specs(
    airports: list[str] | None,
    origins: list[str] | None,
    destinations: list[str] | None,
    callsigns: list[str] | None,
    icao24s: list[str] | None,
) -> list[dict[str, str]]:
    """
    """
    if airports:
        return [{"airport": code} for code in airports]

    if origins and destinations:
        return [
            {"departure_airport": origin, "arrival_airport": destination}
            for origin in origins
            for destination in destinations
        ]

    if origins:
        return [{"departure_airport": origin} for origin in origins]

    if destinations:
        return [{"arrival_airport": destination} for destination in destinations]

    if callsigns:
        return [{"callsign": callsign} for callsign in callsigns]

    if icao24s:
        return [{"icao24": icao24} for icao24 in icao24s]

    return []


# ============================================================================
# CLASS
# ============================================================================
class OpenSkyService:
    """
    """

    def __init__(
        self,
        trino: Trino,
        airport_service: AirportService,
    ) -> None:
        """
        """
        self.trino: Trino = trino
        self.airport_service: AirportService = airport_service

    def import_fleet_for_period(
        self,
        begin: datetime,
        end: datetime,
        max_flights: int = 5,
        airports: list[str] | None = None,
        origins: list[str] | None = None,
        destinations: list[str] | None = None,
        callsigns: list[str] | None = None,
        icao24s: list[str] | None = None,
        min_altitude_ft: float | None = None,
        max_altitude_ft: float | None = None,
        min_ground_speed_kmh: float | None = None,
        min_duration_seconds: float | None = None,
    ) -> list[AircraftEntity]:
        """
        """
        query_specs = _build_query_specs(airports, origins, destinations, callsigns, icao24s)

        if not query_specs:
            return []

        quotas = _distribute_quotas(len(query_specs), max_flights)

        selected_batches: list[pd.DataFrame] = []
        for query_kwargs, quota in zip(query_specs, quotas):
            if quota <= 0:
                continue

            batch = self._select_flights_for_query(query_kwargs, begin, end, quota)
            if batch is not None:
                selected_batches.append(batch)

        if not selected_batches:
            return []

        combined_flights = cast(pd.DataFrame, pd.concat(selected_batches, ignore_index = True))
        combined_flights = combined_flights.drop_duplicates(subset = ["icao24", "firstseen"])

        history_df = self._fetch_combined_history(combined_flights)

        if history_df is None or history_df.empty:
            return []

        history_by_icao24: dict[str, pd.DataFrame] = {
            str(icao24): group for icao24, group in history_df.groupby("icao24")
        }

        reference_time = begin.timestamp()

        fleet: list[AircraftEntity] = []
        for _, flight_row in combined_flights.iterrows():
            aircraft = self._build_aircraft_for_flight(flight_row, history_by_icao24, reference_time)
            if aircraft is not None:
                fleet.append(aircraft)

        return self._apply_post_filters(
            fleet,
            min_altitude_ft = min_altitude_ft,
            max_altitude_ft = max_altitude_ft,
            min_ground_speed_kmh = min_ground_speed_kmh,
            min_duration_seconds = min_duration_seconds,
        )

    @staticmethod
    def _apply_post_filters(
        fleet: list[AircraftEntity],
        min_altitude_ft: float | None,
        max_altitude_ft: float | None,
        min_ground_speed_kmh: float | None,
        min_duration_seconds: float | None,
    ) -> list[AircraftEntity]:
        """
        """
        filtered: list[AircraftEntity] = []

        for aircraft in fleet:
            trajectory = aircraft.trajectory

            if min_altitude_ft is not None and trajectory.get_max_altitude_ft() < min_altitude_ft:
                continue

            if max_altitude_ft is not None and trajectory.get_max_altitude_ft() > max_altitude_ft:
                continue

            if min_ground_speed_kmh is not None and trajectory.get_max_ground_speed_kmh() < min_ground_speed_kmh:
                continue

            if min_duration_seconds is not None and trajectory.get_duration_seconds() < min_duration_seconds:
                continue

            filtered.append(aircraft)

        return filtered

    def _select_flights_for_query(
        self,
        query_kwargs: dict[str, str],
        begin: datetime,
        end: datetime,
        quota: int,
    ) -> pd.DataFrame | None:
        """
        """
        try:
            flightlist_df = self.trino.flightlist(begin, end, **query_kwargs)
        except (TrinoError, OSError):
            logger.exception("flightlist query failed for %s", query_kwargs)
            return None

        if flightlist_df is None or flightlist_df.empty:
            return None

        valid_flights = self._filter_valid_flights(flightlist_df)

        if valid_flights.empty:
            return None

        return valid_flights.head(quota).copy()

    @staticmethod
    def _filter_valid_flights(
            flights_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        """
        mask = (
                flights_df["icao24"].apply(lambda v: isinstance(v, str))
                & flights_df["firstseen"].notna()
                & flights_df["lastseen"].notna()
                & flights_df["departure"].apply(lambda v: isinstance(v, str))
                & flights_df["arrival"].apply(lambda v: isinstance(v, str))
        )
        return flights_df[mask]

    def _fetch_combined_history(
        self,
        flights_df: pd.DataFrame,
    ) -> pd.DataFrame | None:
        """
        """
        icao24_list = flights_df["icao24"].unique().tolist()
        overall_begin = flights_df["firstseen"].apply(_to_unix_seconds).min()
        overall_end = flights_df["lastseen"].apply(_to_unix_seconds).max()

        try:
            history_df = self.trino.history(overall_begin, overall_end, icao24=icao24_list)
        except (TrinoError, OSError):
            logger.exception("history query failed for %s", icao24_list)
            return None

        if history_df is None or history_df.empty:
            return None

        history_df = history_df.dropna(
            subset = ["time", "lat", "lon", "baroaltitude", "onground", "icao24"]
        ).copy()

        history_df["time_unix"] = history_df["time"].apply(_to_unix_seconds)
        history_df = history_df.sort_values("time_unix").reset_index(drop = True)

        return history_df

    def _resolve_airport(
        self,
        code: object,
    ) -> AirportEntity:
        """
        """
        if not isinstance(code, str):
            return AirportEntity.unknown()

        airport_info = self.airport_service.get_airport(code)
        return airport_info if airport_info is not None else AirportEntity.unknown()

    def _build_aircraft_for_flight(
        self,
        flight_row: pd.Series,
        history_by_icao24: dict[str, pd.DataFrame],
        reference_time: float,
    ) -> AircraftEntity | None:
        """
        """
        icao24 = str(flight_row["icao24"])
        first_seen = _to_unix_seconds(flight_row["firstseen"])
        last_seen = _to_unix_seconds(flight_row["lastseen"])

        aircraft_history = history_by_icao24.get(icao24)
        if aircraft_history is None:
            logger.warning("Skipping %s: no history data", icao24)
            return None

        flight_history = aircraft_history[
            (aircraft_history["time_unix"] >= first_seen)
            & (aircraft_history["time_unix"] <= last_seen)
        ]

        if len(flight_history) < 2:
            logger.warning("Skipping %s: no usable history", icao24)
            return None

        trajectory_points: list[TrajectoryPointEntity] = []
        for _, row in flight_history.iterrows():
            velocity = row["velocity"] if pd.notna(row["velocity"]) else 0.0
            vertrate = row["vertrate"] if pd.notna(row["vertrate"]) else 0.0

            trajectory_points.append(
                TrajectoryPointEntity(
                    time_offset_seconds = row["time_unix"] - reference_time,
                    lat = float(row["lat"]),
                    lon = float(row["lon"]),
                    altitude_ft = float(row["baroaltitude"]) / METERS_PER_FOOT,
                    ground_speed_kmh = float(velocity) * MS_TO_KMH,
                    vertical_rate_ft_per_min = float(vertrate) * MS_TO_FT_PER_MIN,
                    on_ground = bool(row["onground"])
                )
            )

        trajectory = TrajectoryEntity(points = trajectory_points)

        callsign_raw = flight_row.get("callsign")
        callsign = callsign_raw.strip() if isinstance(callsign_raw, str) else "UNKNOWN"

        origin_airport = self._resolve_airport(flight_row.get("departure"))
        destination_airport = self._resolve_airport(flight_row.get("arrival"))

        return AircraftEntity(
            callsign = callsign,
            origin_airport = origin_airport,
            destination_airport = destination_airport,
            trajectory = trajectory
        )
