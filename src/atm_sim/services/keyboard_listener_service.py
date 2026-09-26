""" """

# ============================================================================
# IMPORT
# ============================================================================
import sys
from typing import Any


# ============================================================================
# CLASS
# ============================================================================
class KeyboardListenerService:
    """ """

    def __init__(self) -> None:
        """ """
        self._old_settings: list[Any] | None = None
        self._interactive: bool = True

    def start(self) -> None:
        """ """
        if sys.platform == "win32":
            return

        import termios
        import tty

        try:
            fd = sys.stdin.fileno()
            self._old_settings = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        except OSError:
            self._interactive = False

    def stop(self) -> None:
        """ """
        if sys.platform == "win32" or not self._interactive or self._old_settings is None:
            return

        import termios

        fd = sys.stdin.fileno()
        termios.tcsetattr(fd, termios.TCSADRAIN, self._old_settings)

    def read_key_nonblocking(self) -> str | None:
        """ """
        if not self._interactive:
            return None

        if sys.platform == "win32":
            return self._read_key_windows()
        return self._read_key_unix()

    @staticmethod
    def _read_key_windows() -> str | None:
        """ """
        if sys.platform != "win32":
            return None

        import msvcrt

        if msvcrt.kbhit():
            raw = msvcrt.getch()
            return raw.decode(errors="ignore").lower()
        return None

    @staticmethod
    def _read_key_unix() -> str | None:
        """ """
        import select

        ready, _, _ = select.select([sys.stdin], [], [], 0)
        if ready:
            return sys.stdin.read(1).lower()
        return None
