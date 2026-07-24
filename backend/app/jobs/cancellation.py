"""
app/jobs/cancellation.py — CancellationToken

Thread-safe cooperative cancellation mechanism.
The executor checks the token between stages; stages may check it internally
at long-running points if they choose to cooperate more granularly.
"""
import threading


class CancellationToken:
    """Thread-safe cooperative cancellation token."""

    def __init__(self) -> None:
        self._cancelled = False
        self._lock = threading.Lock()

    def cancel(self) -> None:
        """Signal cancellation. Idempotent."""
        with self._lock:
            self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        with self._lock:
            return self._cancelled

    def raise_if_cancelled(self) -> None:
        """Raise CancelledError if cancellation was requested."""
        if self.is_cancelled:
            raise CancelledError("Job was cancelled by request.")


class CancelledError(Exception):
    """Raised when cooperative cancellation is detected."""
