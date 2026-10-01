""" """

# ============================================================================
# IMPORT
# ============================================================================
import sys

import pytest

# SERVICES IMPORT
from atm_sim.services.keyboard_listener_service import KeyboardListenerService


# ============================================================================
# TESTS — portable (no platform-specific import)
# ============================================================================
def test_is_interactive_defaults_to_true() -> None:
    """ """
    service = KeyboardListenerService()

    assert service.is_interactive() is True


def test_read_key_nonblocking_returns_none_when_not_interactive() -> None:
    """ """
    service = KeyboardListenerService()
    service._interactive = False  # noqa: SLF001

    assert service.read_key_nonblocking() is None


def test_stop_without_start_is_a_noop() -> None:
    """ """
    service = KeyboardListenerService()

    service.stop()


# ============================================================================
# TESTS — POSIX (termios/tty/select)
# ============================================================================
@pytest.mark.skipif(sys.platform == "win32", reason="exercises termios, POSIX only")
def test_start_configures_terminal_and_stop_restores_it(monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    import termios
    import tty

    calls: list[str] = []
    # noinspection PyUnresolvedReferences
    monkeypatch.setattr(sys.stdin, "fileno", lambda: 0)
    monkeypatch.setattr(termios, "tcgetattr", lambda _fd: ["fake-settings"])
    monkeypatch.setattr(tty, "setcbreak", lambda _fd: calls.append("setcbreak"))
    monkeypatch.setattr(termios, "tcsetattr", lambda _fd, _when, _settings: calls.append("tcsetattr"))

    service = KeyboardListenerService()
    service.start()

    assert service.is_interactive() is True
    assert calls == ["setcbreak"]

    service.stop()

    assert calls == ["setcbreak", "tcsetattr"]


@pytest.mark.skipif(sys.platform == "win32", reason="exercises termios, POSIX only")
def test_start_sets_not_interactive_on_oserror(monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    import termios

    def _raise(_fd: int) -> list[object]:
        raise OSError("not a tty")

    monkeypatch.setattr(termios, "tcgetattr", _raise)

    service = KeyboardListenerService()
    service.start()

    assert service.is_interactive() is False


@pytest.mark.skipif(sys.platform == "win32", reason="exercises select, POSIX only")
def test_read_key_unix_returns_none_when_nothing_pending(monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    import select as select_module

    service = KeyboardListenerService()
    service._interactive = True  # noqa: SLF001

    monkeypatch.setattr(select_module, "select", lambda *_args, **_kwargs: ([], [], []))

    assert service.read_key_nonblocking() is None


@pytest.mark.skipif(sys.platform == "win32", reason="exercises select, POSIX only")
def test_read_key_unix_returns_lowercased_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    import select as select_module

    service = KeyboardListenerService()
    service._interactive = True  # noqa: SLF001

    monkeypatch.setattr(select_module, "select", lambda *_args, **_kwargs: ([sys.stdin], [], []))
    # noinspection PyUnresolvedReferences
    monkeypatch.setattr(sys.stdin, "read", lambda _n: "A")

    assert service.read_key_nonblocking() == "a"


@pytest.mark.skipif(sys.platform == "win32", reason="checks the off-windows guard of a windows-only helper")
def test_read_key_windows_static_returns_none_off_windows() -> None:
    """ """
    assert KeyboardListenerService._read_key_windows() is None  # noqa: SLF001


# ============================================================================
# TESTS — Windows (msvcrt)
# ============================================================================
@pytest.mark.skipif(sys.platform != "win32", reason="exercises msvcrt, Windows only")
def test_read_key_windows_returns_none_when_no_key_pressed(monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    import msvcrt

    monkeypatch.setattr(msvcrt, "kbhit", lambda: False)

    service = KeyboardListenerService()

    assert service.read_key_nonblocking() is None


@pytest.mark.skipif(sys.platform != "win32", reason="exercises msvcrt, Windows only")
def test_read_key_windows_returns_lowercased_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """ """
    import msvcrt

    monkeypatch.setattr(msvcrt, "kbhit", lambda: True)
    monkeypatch.setattr(msvcrt, "getch", lambda: b"A")

    service = KeyboardListenerService()

    assert service.read_key_nonblocking() == "a"
