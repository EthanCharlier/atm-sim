""" """

# ============================================================================
# IMPORT
# ============================================================================
from datetime import UTC, datetime, timedelta

import time
import pytest

# CONSTANTS IMPORT
from atm_sim.constants.constants import ENTER_KEY, IDLE_SLEEP_SECONDS, PAUSE_KEY, QUIT_KEY, SPEED_DOWN_KEY, SPEED_UP_KEY

# ENTITIES IMPORT
from atm_sim.entities.aircraft_entity import AircraftEntity
from atm_sim.entities.airport_entity import AirportEntity
from atm_sim.entities.clock_entity import SimClockEntity
from atm_sim.entities.simulation_engine_entity import SimulationEngineEntity
from atm_sim.entities.trajectory_entity import TrajectoryEntity
from atm_sim.entities.trajectory_point_entity import TrajectoryPointEntity

# ENUMS IMPORT
from atm_sim.enums.simulation_status_enum import SimulationStatusEnum

# EXCEPTIONS IMPORT
from atm_sim.exceptions.exceptions import InvalidSimulationPeriodError, MultipleSelectionModesError

# SERVICES IMPORT
from atm_sim.services import simulation_service as service_module
from atm_sim.services.simulation_service import SimulationService
from atm_sim.services.console_renderer_service import ConsoleRendererService


# ============================================================================
# HELPERS / FAKES
# ============================================================================
class _FakeAirportService:
    """ """

    def __init__(self, airports: dict[str, AirportEntity] | None = None) -> None:
        """ """
        self._airports = airports or {}

    def get_airport(self, icao: str) -> AirportEntity | None:
        """ """
        return self._airports.get(icao.upper())


class _FakeOpenSkyService:
    """ """

    def __init__(self, fleet: list[AircraftEntity] | None = None) -> None:
        """ """
        self._fleet = fleet if fleet is not None else []
        self.calls: list[dict[str, object]] = []

    def import_fleet_for_period(self, **kwargs: object) -> list[AircraftEntity]:
        """ """
        self.calls.append(kwargs)
        return self._fleet


class _FakeKeyboardListener:
    """ """

    def __init__(self, keys: list[str | None], interactive: bool = True) -> None:
        """ """
        self._keys = list(keys)
        self._interactive = interactive
        self.start_calls = 0
        self.stop_calls = 0

    def start(self) -> None:
        """ """
        self.start_calls += 1

    def stop(self) -> None:
        """ """
        self.stop_calls += 1

    def is_interactive(self) -> bool:
        """ """
        return self._interactive

    def read_key_nonblocking(self) -> str | None:
        """ """
        if self._keys:
            return self._keys.pop(0)
        return None


def _make_aircraft(callsign: str = "AFR123", duration_seconds: float = 100.0) -> AircraftEntity:
    """ """
    points = [
        TrajectoryPointEntity(
            time_offset_seconds=0.0, lat=0.0, lon=0.0, altitude_ft=0.0,
            ground_speed_kmh=0.0, vertical_rate_ft_per_min=0.0, on_ground=True,
        ),
        TrajectoryPointEntity(
            time_offset_seconds=duration_seconds, lat=1.0, lon=1.0, altitude_ft=1000.0,
            ground_speed_kmh=500.0, vertical_rate_ft_per_min=0.0, on_ground=False,
        ),
    ]
    return AircraftEntity(
        callsign=callsign,
        origin_airport=AirportEntity.unknown(),
        destination_airport=AirportEntity.unknown(),
        trajectory=TrajectoryEntity(points=points),
    )


def _make_simulation_service(
    opensky_service: _FakeOpenSkyService | None = None,
    airport_service: _FakeAirportService | None = None,
) -> SimulationService:
    """ """
    return SimulationService(
        opensky_service=opensky_service or _FakeOpenSkyService(),  # type: ignore[arg-type]
        airport_service=airport_service or _FakeAirportService(),  # type: ignore[arg-type]
    )


# ============================================================================
# TESTS — _validate_selection_mode
# ============================================================================
def test_validate_selection_mode_allows_no_selection() -> None:
    """ """
    SimulationService._validate_selection_mode(None, None, None, None, None)  # noqa: SLF001


def test_validate_selection_mode_allows_single_mode() -> None:
    """ """
    SimulationService._validate_selection_mode(["LFBO"], None, None, None, None)  # noqa: SLF001


def test_validate_selection_mode_allows_origin_destination_as_one_mode() -> None:
    """ """
    SimulationService._validate_selection_mode(None, ["LFBO"], ["LFPO"], None, None)  # noqa: SLF001


def test_validate_selection_mode_rejects_multiple_modes() -> None:
    """ """
    with pytest.raises(MultipleSelectionModesError):
        SimulationService._validate_selection_mode(["LFBO"], None, None, ["AFR123"], None)  # noqa: SLF001


# ============================================================================
# TESTS — _format_selection_label / _airport_display_name
# ============================================================================
def test_airport_display_name_known_airport() -> None:
    """ """
    airport = AirportEntity.unknown()
    airport.icao = "LFBO"
    airport.name = "Toulouse-Blagnac"
    service = _make_simulation_service(airport_service=_FakeAirportService({"LFBO": airport}))

    assert service._airport_display_name("LFBO") == "Toulouse-Blagnac (LFBO)"  # noqa: SLF001


def test_airport_display_name_unknown_returns_code() -> None:
    """ """
    service = _make_simulation_service()

    assert service._airport_display_name("ZZZZ") == "ZZZZ"  # noqa: SLF001


def test_format_selection_label_airports() -> None:
    """ """
    service = _make_simulation_service()

    label = service._format_selection_label(["LFBO", "LFPG"], None, None, None, None)  # noqa: SLF001

    assert label == "LFBO / LFPG"


def test_format_selection_label_origin_destination() -> None:
    """ """
    service = _make_simulation_service()

    label = service._format_selection_label(None, ["LFBO"], ["LFPG"], None, None)  # noqa: SLF001

    assert label == "LFBO -> LFPG"


def test_format_selection_label_origins_only() -> None:
    """ """
    service = _make_simulation_service()

    label = service._format_selection_label(None, ["LFBO"], None, None, None)  # noqa: SLF001

    assert label == "departures from LFBO"


def test_format_selection_label_destinations_only() -> None:
    """ """
    service = _make_simulation_service()

    label = service._format_selection_label(None, None, ["LFPG"], None, None)  # noqa: SLF001

    assert label == "arrivals to LFPG"


def test_format_selection_label_callsigns() -> None:
    """ """
    service = _make_simulation_service()

    label = service._format_selection_label(None, None, None, ["AFR123", "RYR456"], None)  # noqa: SLF001

    assert label == "callsign(s) AFR123 / RYR456"


def test_format_selection_label_icao24s() -> None:
    """ """
    service = _make_simulation_service()

    label = service._format_selection_label(None, None, None, None, ["3944ef"])  # noqa: SLF001

    assert label == "aircraft 3944ef"


def test_format_selection_label_defaults_when_nothing_given() -> None:
    """ """
    service = _make_simulation_service()

    label = service._format_selection_label(None, None, None, None, None)  # noqa: SLF001

    assert label == "LFBO"


# ============================================================================
# TESTS — _compute_statistics
# ============================================================================
def test_compute_statistics_with_empty_fleet() -> None:
    """ """
    statistics = SimulationService._compute_statistics([], final_elapsed_seconds=0.0)  # noqa: SLF001

    assert statistics.total_flights == 0
    assert statistics.average_duration_seconds == pytest.approx(0.0)


def test_compute_statistics_with_fleet() -> None:
    """ """
    aircraft = _make_aircraft(duration_seconds=100.0)
    aircraft.update(50.0)

    statistics = SimulationService._compute_statistics([aircraft], final_elapsed_seconds=50.0)  # noqa: SLF001

    assert statistics.total_flights == 1
    assert statistics.per_aircraft[0].callsign == "AFR123"
    assert statistics.per_aircraft[0].type_code == "?"
    assert statistics.average_duration_seconds == pytest.approx(50.0)
    assert statistics.max_altitude_ft == pytest.approx(0.0)


# ============================================================================
# TESTS — _handle_key_input
# ============================================================================
def test_handle_key_input_pause_then_resume() -> None:
    """ """
    engine = SimulationEngineEntity(clock=SimClockEntity(tick_seconds=1.0))

    SimulationService._handle_key_input(PAUSE_KEY, engine)  # noqa: SLF001
    assert engine.clock.is_paused() is True

    SimulationService._handle_key_input(PAUSE_KEY, engine)  # noqa: SLF001
    assert engine.clock.is_paused() is False


def test_handle_key_input_speed_up_and_down() -> None:
    """ """
    engine = SimulationEngineEntity(clock=SimClockEntity(tick_seconds=1.0))
    initial_factor = engine.clock.speed_factor

    SimulationService._handle_key_input(SPEED_UP_KEY, engine)  # noqa: SLF001
    assert engine.clock.speed_factor > initial_factor

    SimulationService._handle_key_input(SPEED_DOWN_KEY, engine)  # noqa: SLF001
    assert engine.clock.speed_factor == pytest.approx(initial_factor)


def test_handle_key_input_unknown_key_is_noop() -> None:
    """ """
    engine = SimulationEngineEntity(clock=SimClockEntity(tick_seconds=1.0))

    SimulationService._handle_key_input("z", engine)  # noqa: SLF001

    assert engine.clock.is_paused() is False


# ============================================================================
# TESTS — _advance_and_get_status
# ============================================================================
def test_advance_and_get_status_ticks_when_running() -> None:
    """ """
    engine = SimulationEngineEntity(clock=SimClockEntity(tick_seconds=10.0))

    status = SimulationService._advance_and_get_status(engine, total_duration_seconds=100.0)  # noqa: SLF001

    assert status == SimulationStatusEnum.RUNNING
    assert engine.clock.sim_time_elapsed == pytest.approx(10.0)


def test_advance_and_get_status_does_not_tick_when_paused() -> None:
    """ """
    engine = SimulationEngineEntity(clock=SimClockEntity(tick_seconds=10.0))
    engine.clock.pause()

    SimulationService._advance_and_get_status(engine, total_duration_seconds=100.0)  # noqa: SLF001

    assert engine.clock.sim_time_elapsed == pytest.approx(0.0)


def test_advance_and_get_status_returns_complete_at_duration() -> None:
    """ """
    engine = SimulationEngineEntity(clock=SimClockEntity(tick_seconds=100.0))

    status = SimulationService._advance_and_get_status(engine, total_duration_seconds=100.0)  # noqa: SLF001

    assert status == SimulationStatusEnum.COMPLETE


# ============================================================================
# TESTS — _maybe_render
# ============================================================================
def test_maybe_render_renders_on_complete_regardless_of_interval(monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    engine = SimulationEngineEntity(clock=SimClockEntity(tick_seconds=1.0))
    render_calls: list[object] = []
    monkeypatch.setattr(ConsoleRendererService, "render", lambda *a, **k: render_calls.append(a))
    monkeypatch.setattr(time, "monotonic", lambda: 1000.0)

    result = SimulationService._maybe_render(  # noqa: SLF001
        engine=engine, airport_label="LFBO", begin=datetime(2026, 9, 1, tzinfo=UTC),
        status=SimulationStatusEnum.COMPLETE, last_render_time=999.999,
    )

    assert result == 1000.0
    assert len(render_calls) == 1


def test_maybe_render_skips_when_interval_not_elapsed(monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    engine = SimulationEngineEntity(clock=SimClockEntity(tick_seconds=1.0))
    render_calls: list[object] = []
    monkeypatch.setattr(ConsoleRendererService, "render", lambda *a, **k: render_calls.append(a))
    monkeypatch.setattr(time, "monotonic", lambda: 1000.0)

    result = SimulationService._maybe_render(  # noqa: SLF001
        engine=engine, airport_label="LFBO", begin=datetime(2026, 9, 1, tzinfo=UTC),
        status=SimulationStatusEnum.RUNNING, last_render_time=999.99,
    )

    assert result == 999.99
    assert render_calls == []


# ============================================================================
# TESTS — _sleep_for_status
# ============================================================================
def test_sleep_for_status_running_uses_tick_over_speed(monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    engine = SimulationEngineEntity(clock=SimClockEntity(tick_seconds=2.0))
    sleep_calls: list[float] = []
    monkeypatch.setattr(time, "sleep", sleep_calls.append)

    SimulationService._sleep_for_status(SimulationStatusEnum.RUNNING, engine)  # noqa: SLF001

    assert sleep_calls == [pytest.approx(2.0)]


def test_sleep_for_status_idle_uses_idle_sleep_seconds(monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    engine = SimulationEngineEntity(clock=SimClockEntity(tick_seconds=2.0))
    sleep_calls: list[float] = []
    monkeypatch.setattr(time, "sleep", sleep_calls.append)

    SimulationService._sleep_for_status(SimulationStatusEnum.PAUSED, engine)  # noqa: SLF001

    assert sleep_calls == [pytest.approx(IDLE_SLEEP_SECONDS)]


# ============================================================================
# TESTS — _compute_yesterday_utc_range
# ============================================================================
def test_compute_yesterday_utc_range() -> None:
    """ """
    start, end = SimulationService._compute_yesterday_utc_range()  # noqa: SLF001

    assert end - start == timedelta(days=1)
    assert end.hour == 0
    assert end.minute == 0
    assert end.second == 0
    assert end.tzinfo == UTC


# ============================================================================
# TESTS — _wait_for_summary_choice
# ============================================================================
def test_wait_for_summary_choice_returns_true_when_not_interactive() -> None:
    """ """
    listener = _FakeKeyboardListener(keys=[], interactive=False)

    assert SimulationService._wait_for_summary_choice(listener) is True  # type: ignore[arg-type]  # noqa: SLF001


def test_wait_for_summary_choice_returns_false_on_quit() -> None:
    """ """
    listener = _FakeKeyboardListener(keys=[QUIT_KEY])

    assert SimulationService._wait_for_summary_choice(listener) is False  # type: ignore[arg-type]  # noqa: SLF001


def test_wait_for_summary_choice_returns_true_on_enter(monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    monkeypatch.setattr(time, "sleep", lambda _s: None)
    listener = _FakeKeyboardListener(keys=[None, ENTER_KEY])

    assert SimulationService._wait_for_summary_choice(listener) is True  # type: ignore[arg-type]  # noqa: SLF001


# ============================================================================
# TESTS — start() orchestration (mocking _run)
# ============================================================================
def test_start_rejects_multiple_selection_modes() -> None:
    """ """
    service = _make_simulation_service()

    with pytest.raises(MultipleSelectionModesError):
        service.start(airports=["LFBO"], callsigns=["AFR123"])


def test_start_rejects_invalid_period() -> None:
    """ """
    service = _make_simulation_service()
    begin = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
    end = datetime(2026, 9, 1, 6, 0, tzinfo=UTC)

    with pytest.raises(InvalidSimulationPeriodError):
        service.start(begin=begin, end=end)


def test_start_defaults_to_lfbo_airport(monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    opensky = _FakeOpenSkyService(fleet=[])
    service = _make_simulation_service(opensky_service=opensky)

    service.start(begin=datetime(2026, 9, 1, 6, 0, tzinfo=UTC), end=datetime(2026, 9, 1, 8, 0, tzinfo=UTC))

    assert opensky.calls[0]["airports"] == ["LFBO"]


def test_start_prints_and_returns_when_fleet_empty(capsys: pytest.CaptureFixture[str]) -> None:
    """ """
    opensky = _FakeOpenSkyService(fleet=[])
    service = _make_simulation_service(opensky_service=opensky)

    service.start(begin=datetime(2026, 9, 1, 6, 0, tzinfo=UTC), end=datetime(2026, 9, 1, 8, 0, tzinfo=UTC))

    captured = capsys.readouterr()
    assert "No aircraft to simulate" in captured.out


def test_start_calls_run_with_fleet(monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    aircraft = _make_aircraft()
    opensky = _FakeOpenSkyService(fleet=[aircraft])
    service = _make_simulation_service(opensky_service=opensky)

    run_calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        SimulationService, "_run", staticmethod(lambda **kwargs: run_calls.append(kwargs)),
    )

    service.start(
        airports=["LFBO"],
        begin=datetime(2026, 9, 1, 6, 0, tzinfo=UTC),
        end=datetime(2026, 9, 1, 8, 0, tzinfo=UTC),
        speed_factor=100.0,
    )

    assert len(run_calls) == 1
    assert run_calls[0]["fleet"] == [aircraft]
    assert run_calls[0]["speed_index"] == 5  # resolve_speed_index(100) -> nearest to 60 (index 5)


def test_start_uses_yesterday_range_when_period_not_given(monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    opensky = _FakeOpenSkyService(fleet=[])
    service = _make_simulation_service(opensky_service=opensky)

    service.start()

    begin = opensky.calls[0]["begin"]
    end = opensky.calls[0]["end"]
    assert end - begin == timedelta(days=1)  # type: ignore[operator]


# ============================================================================
# TESTS — _run() end-to-end (scripted keyboard listener, no real sleep)
# ============================================================================
def test_run_quits_immediately_and_skips_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    listener = _FakeKeyboardListener(keys=[QUIT_KEY, QUIT_KEY])
    # noinspection PyUnresolvedReferences
    monkeypatch.setattr(service_module, "KeyboardListenerService", lambda: listener)

    aircraft = _make_aircraft()

    SimulationService._run(  # noqa: SLF001
        fleet=[aircraft],
        airport_label="LFBO",
        begin=datetime(2026, 9, 1, 6, 0, tzinfo=UTC),
        end=datetime(2026, 9, 1, 8, 0, tzinfo=UTC),
        tick_seconds=1.0,
        speed_index=3,
    )

    assert listener.start_calls == 2
    assert listener.stop_calls == 2


def test_run_quits_and_shows_summary(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """ """
    listener = _FakeKeyboardListener(keys=[QUIT_KEY, ENTER_KEY])
    # noinspection PyUnresolvedReferences
    monkeypatch.setattr(service_module, "KeyboardListenerService", lambda: listener)

    aircraft = _make_aircraft()

    SimulationService._run(  # noqa: SLF001
        fleet=[aircraft],
        airport_label="LFBO",
        begin=datetime(2026, 9, 1, 6, 0, tzinfo=UTC),
        end=datetime(2026, 9, 1, 8, 0, tzinfo=UTC),
        tick_seconds=1.0,
        speed_index=3,
    )

    captured = capsys.readouterr()
    assert "OpenSky ATM Simulation summary" in captured.out


def test_run_processes_one_tick_before_quitting(monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    monkeypatch.setattr(time, "sleep", lambda _s: None)
    listener = _FakeKeyboardListener(keys=[None, QUIT_KEY, QUIT_KEY])
    # noinspection PyUnresolvedReferences
    monkeypatch.setattr(service_module, "KeyboardListenerService", lambda: listener)

    aircraft = _make_aircraft(duration_seconds=1000.0)

    SimulationService._run(  # noqa: SLF001
        fleet=[aircraft],
        airport_label="LFBO",
        begin=datetime(2026, 9, 1, 6, 0, tzinfo=UTC),
        end=datetime(2026, 9, 1, 8, 0, tzinfo=UTC),
        tick_seconds=1.0,
        speed_index=3,
    )

    assert listener.start_calls == 2
    assert listener.stop_calls == 2


def test_run_breaks_when_simulation_completes(monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    monkeypatch.setattr(time, "sleep", lambda _s: None)
    listener = _FakeKeyboardListener(keys=[None, QUIT_KEY])
    # noinspection PyUnresolvedReferences
    monkeypatch.setattr(service_module, "KeyboardListenerService", lambda: listener)

    aircraft = _make_aircraft(duration_seconds=100.0)

    SimulationService._run(  # noqa: SLF001
        fleet=[aircraft],
        airport_label="LFBO",
        begin=datetime(2026, 9, 1, 6, 0, 0, tzinfo=UTC),
        end=datetime(2026, 9, 1, 6, 1, 40, tzinfo=UTC),  # exactly 100 seconds later
        tick_seconds=100.0,
        speed_index=3,
    )

    assert listener.start_calls == 2
    assert listener.stop_calls == 2
