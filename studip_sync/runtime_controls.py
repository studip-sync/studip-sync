import select
import sys
import threading
import time

from studip_sync.log import get_logger

try:
    import termios
    import tty
except ImportError:  # pragma: no cover
    termios = None
    tty = None


LOGGER = get_logger(__name__)


class UserAbortError(RuntimeError):
    pass


class RuntimeControls:
    def __init__(self, enabled=True):
        self._enabled_requested = enabled
        self._enabled = False
        self._paused = False
        self._abort_requested = False
        self._paused_hint_shown = False
        self._stop_event = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self._fd = None
        self._old_tty_state = None

    @property
    def enabled(self):
        return self._enabled

    def start(self):
        if self._enabled:
            return True

        if not self._enabled_requested:
            return False

        if termios is None or tty is None:
            return False

        if not hasattr(sys.stdin, "isatty") or not sys.stdin.isatty():
            return False

        try:
            self._fd = sys.stdin.fileno()
            self._old_tty_state = termios.tcgetattr(self._fd)
            tty.setcbreak(self._fd)
        except Exception:
            self._fd = None
            self._old_tty_state = None
            return False

        self._enabled = True
        self._thread = threading.Thread(target=self._input_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=0.5)

        if self._enabled and self._fd is not None and self._old_tty_state is not None:
            try:
                termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old_tty_state)
            except Exception:
                pass

        self._enabled = False
        self._thread = None
        self._fd = None
        self._old_tty_state = None
        self._stop_event.clear()

    def _input_loop(self):
        while not self._stop_event.is_set():
            try:
                ready, _, _ = select.select([sys.stdin], [], [], 0.2)
                if not ready:
                    continue

                key = sys.stdin.read(1).lower()
            except Exception:
                return

            with self._lock:
                if key == "p":
                    self._paused = not self._paused
                    if self._paused:
                        LOGGER.warning("Paused by user. Press 'p' to resume or 'q' to abort.")
                    else:
                        LOGGER.info("Resumed.")
                        self._paused_hint_shown = False
                elif key == "q":
                    self._abort_requested = True
                    LOGGER.warning("Abort requested by user. Stopping gracefully...")
                elif key == "h":
                    LOGGER.info("Controls: [p] pause/resume, [q] abort, [h] help")

    def checkpoint(self):
        if not self._enabled:
            return

        with self._lock:
            abort_requested = self._abort_requested
            paused = self._paused

        if abort_requested:
            raise UserAbortError("Sync aborted by user")

        while paused:
            if not self._paused_hint_shown:
                LOGGER.warning("Paused. Press 'p' to resume or 'q' to abort.")
                self._paused_hint_shown = True

            time.sleep(0.2)

            with self._lock:
                abort_requested = self._abort_requested
                paused = self._paused

            if abort_requested:
                raise UserAbortError("Sync aborted by user")
