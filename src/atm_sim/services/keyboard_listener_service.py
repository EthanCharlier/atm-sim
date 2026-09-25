"""
"""

# ============================================================================
# IMPORT
# ============================================================================
import sys


# ============================================================================
# CLASS
# ============================================================================
class KeyboardListenerService:
    """
    """

    def __init__(self) -> None:
        """
        """
        self._is_windows: bool = sys.platform.startswith("win")
        self._old_settings = None
        self._interactive: bool = True

    def start(self) -> None:
        """
        """
        if self._is_windows:
            return

        try:
            import termios
            import tty

            fd = sys.stdin.fileno()
            self._old_settings = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        except Exception:
            self._interactive = False

    def stop(self) -> None:
        """
        """
        if self._is_windows or not self._interactive or self._old_settings is None:
            return

        import termios

        fd = sys.stdin.fileno()
        termios.tcsetattr(fd, termios.TCSADRAIN, self._old_settings)

    def read_key_nonblocking(self) -> str | None:
        """
        """
        if not self._interactive:
            return None

        if self._is_windows:
            return self._read_key_windows()
        return self._read_key_unix()

    @staticmethod
    def _read_key_windows() -> str | None:
        """
        """
        import msvcrt

        if msvcrt.kbhit():
            raw = msvcrt.getch()
            try:
                return raw.decode(errors = "ignore").lower()
            except Exception:
                return None
        return None

    @staticmethod
    def _read_key_unix() -> str | None:
        """
        """
        import select

        ready, _, _ = select.select([sys.stdin], [], [], 0)
        if ready:
            return sys.stdin.read(1).lower()
        return None
