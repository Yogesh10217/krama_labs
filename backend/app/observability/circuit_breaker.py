"""
app/observability/circuit_breaker.py — Phase 11 Circuit Breaker

States (per approved spec):
  CLOSED   → normal operation; failures are counted
  OPEN     → calls are blocked; waits for recovery_timeout
  HALF_OPEN → limited calls allowed to test recovery

Expanded metrics:
  - circuit_breaker_transitions_total (provider, from_state, to_state)
  - circuit_breaker_success_total (provider)
  - circuit_breaker_failure_total (provider)
  - circuit_breaker_state gauge (0=CLOSED, 1=OPEN, 2=HALF_OPEN)

Configuration (from Config):
  CB_FAILURE_THRESHOLD   (default: 5)
  CB_RECOVERY_TIMEOUT    (default: 60s)
  CB_HALF_OPEN_MAX_CALLS (default: 3)

Circuit breakers are registered per-provider. Providers:
  ollama, gemini, openai, storage, ocr_paddle, ocr_external
"""

from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, Generator, Optional

from app.core.config import Config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State definitions
# ---------------------------------------------------------------------------

class CBState(str, Enum):
    CLOSED    = "CLOSED"
    OPEN      = "OPEN"
    HALF_OPEN = "HALF_OPEN"


_STATE_GAUGE_VALUE: Dict[CBState, int] = {
    CBState.CLOSED:    0,
    CBState.OPEN:      1,
    CBState.HALF_OPEN: 2,
}


# ---------------------------------------------------------------------------
# Circuit Breaker
# ---------------------------------------------------------------------------

class CircuitBreakerOpen(Exception):
    """Raised when a circuit is OPEN and the call is blocked."""
    def __init__(self, provider: str, retry_after: float) -> None:
        self.provider    = provider
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker OPEN for provider '{provider}'. "
            f"Retry after {retry_after:.1f}s."
        )


@dataclass
class CircuitBreakerStats:
    total_calls:        int = 0
    success_calls:      int = 0
    failure_calls:      int = 0
    consecutive_fails:  int = 0
    consecutive_ok:     int = 0
    transitions:        list = field(default_factory=list)
    state:              CBState = CBState.CLOSED


class CircuitBreaker:
    """
    Per-provider circuit breaker with Prometheus metric integration.

    Thread-safe via internal lock. Metrics are emitted lazily to avoid
    import cycles (metrics registry may not exist when CB is constructed).
    """

    def __init__(
        self,
        provider:           str,
        failure_threshold:  int = 5,
        recovery_timeout:   int = 60,
        half_open_max_calls:int = 3,
    ) -> None:
        self.provider             = provider
        self._failure_threshold   = failure_threshold
        self._recovery_timeout    = recovery_timeout
        self._half_open_max_calls = half_open_max_calls

        self._state               = CBState.CLOSED
        self._failure_count       = 0
        self._success_count       = 0
        self._half_open_calls     = 0
        self._opened_at: Optional[float] = None
        self._lock                = threading.Lock()
        self._stats               = CircuitBreakerStats()

        self._update_gauge()

    # ── Public API ─────────────────────────────────────────────────────────

    @property
    def state(self) -> CBState:
        return self._state

    @property
    def stats(self) -> CircuitBreakerStats:
        return self._stats

    def is_open(self) -> bool:
        """Return True if calls should be blocked (OPEN state)."""
        with self._lock:
            return self._evaluate_state() == CBState.OPEN

    def call(self, fn: Callable, *args, **kwargs):
        """
        Execute fn through the circuit breaker.

        Raises CircuitBreakerOpen if the circuit is OPEN.
        Records success/failure metrics regardless of the function's outcome.
        """
        with self._lock:
            current_state = self._evaluate_state()

        if current_state == CBState.OPEN:
            retry_after = max(
                0.0, self._recovery_timeout - (time.monotonic() - (self._opened_at or 0))
            )
            raise CircuitBreakerOpen(self.provider, retry_after)

        if current_state == CBState.HALF_OPEN:
            with self._lock:
                if self._half_open_calls >= self._half_open_max_calls:
                    # Exceeded probe quota — treat as OPEN
                    raise CircuitBreakerOpen(self.provider, 0.0)
                self._half_open_calls += 1

        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except CircuitBreakerOpen:
            raise
        except Exception as exc:
            self._on_failure()
            raise

    @contextmanager
    def protect(self) -> Generator[None, None, None]:
        """
        Context-manager form of call().

        Usage:
            with cb.protect():
                do_something()
        """
        with self._lock:
            current_state = self._evaluate_state()

        if current_state == CBState.OPEN:
            retry_after = max(
                0.0, self._recovery_timeout - (time.monotonic() - (self._opened_at or 0))
            )
            raise CircuitBreakerOpen(self.provider, retry_after)

        if current_state == CBState.HALF_OPEN:
            with self._lock:
                if self._half_open_calls >= self._half_open_max_calls:
                    raise CircuitBreakerOpen(self.provider, 0.0)
                self._half_open_calls += 1

        try:
            yield
            self._on_success()
        except CircuitBreakerOpen:
            raise
        except Exception:
            self._on_failure()
            raise

    def reset(self) -> None:
        """Manually force back to CLOSED (e.g. after manual provider fix)."""
        with self._lock:
            old = self._state
            self._state         = CBState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
            self._opened_at     = None
            self._stats.consecutive_fails = 0
            self._stats.consecutive_ok    = 0
        if old != CBState.CLOSED:
            self._record_transition(old, CBState.CLOSED)
        self._update_gauge()

    # ── Internal state machine ─────────────────────────────────────────────

    def _evaluate_state(self) -> CBState:
        """Evaluate current state, triggering OPEN → HALF_OPEN transition if timeout elapsed."""
        if self._state == CBState.OPEN:
            if self._opened_at and (time.monotonic() - self._opened_at) >= self._recovery_timeout:
                self._transition_to(CBState.HALF_OPEN)
        return self._state

    def _on_success(self) -> None:
        with self._lock:
            self._stats.total_calls   += 1
            self._stats.success_calls += 1
            self._stats.consecutive_ok   += 1
            self._stats.consecutive_fails = 0
            old_state = self._state
            if self._state == CBState.HALF_OPEN:
                if self._stats.consecutive_ok >= self._half_open_max_calls:
                    self._transition_to(CBState.CLOSED)
            elif self._state == CBState.CLOSED:
                self._failure_count = 0
        self._record_counter("success")
        self._update_gauge()

    def _on_failure(self) -> None:
        with self._lock:
            self._stats.total_calls    += 1
            self._stats.failure_calls  += 1
            self._stats.consecutive_fails += 1
            self._stats.consecutive_ok     = 0
            self._failure_count += 1
            if self._state in (CBState.CLOSED, CBState.HALF_OPEN):
                if self._failure_count >= self._failure_threshold:
                    self._transition_to(CBState.OPEN)
        self._record_counter("failure")
        self._update_gauge()

    def _transition_to(self, new_state: CBState) -> None:
        """Must be called with self._lock held."""
        old_state   = self._state
        self._state = new_state

        if new_state == CBState.OPEN:
            self._opened_at      = time.monotonic()
            self._half_open_calls = 0
        elif new_state == CBState.CLOSED:
            self._failure_count  = 0
            self._opened_at      = None
            self._half_open_calls = 0
        elif new_state == CBState.HALF_OPEN:
            self._failure_count  = 0
            self._half_open_calls = 0
            self._stats.consecutive_ok = 0

        self._stats.state = new_state
        self._stats.transitions.append((old_state.value, new_state.value, time.time()))

        logger.warning(
            "Circuit breaker '%s' transitioned %s → %s",
            self.provider, old_state.value, new_state.value,
        )
        self._record_transition(old_state, new_state)

    # ── Metric helpers ─────────────────────────────────────────────────────

    def _update_gauge(self) -> None:
        """Update the Prometheus state gauge (best-effort)."""
        if not Config.ENABLE_METRICS:
            return
        try:
            from app.observability.metrics import get_metrics_registry
            m = get_metrics_registry()
            m.circuit_breaker_state.labels(provider=self.provider).set(
                _STATE_GAUGE_VALUE[self._state]
            )
        except Exception:
            pass

    def _record_transition(self, old: CBState, new: CBState) -> None:
        if not Config.ENABLE_METRICS:
            return
        try:
            from app.observability.metrics import get_metrics_registry
            m = get_metrics_registry()
            m.circuit_breaker_transitions_total.labels(
                provider=self.provider,
                from_state=old.value,
                to_state=new.value,
            ).inc()
        except Exception:
            pass

    def _record_counter(self, kind: str) -> None:
        if not Config.ENABLE_METRICS:
            return
        try:
            from app.observability.metrics import get_metrics_registry
            m = get_metrics_registry()
            if kind == "success":
                m.circuit_breaker_success_total.labels(provider=self.provider).inc()
            else:
                m.circuit_breaker_failure_total.labels(provider=self.provider).inc()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Registry — singleton map of provider → CircuitBreaker
# ---------------------------------------------------------------------------

class CircuitBreakerRegistry:
    """
    Global registry of circuit breakers, keyed by provider name.

    Provides a single access point so circuit breakers survive across
    requests and workers.
    """

    _PROVIDERS = ["ollama", "gemini", "openai", "storage", "ocr_paddle", "ocr_external"]

    _registry: Dict[str, CircuitBreaker] = {}
    _lock = threading.Lock()

    @classmethod
    def get(cls, provider: str) -> CircuitBreaker:
        """Get or create a circuit breaker for the named provider."""
        if provider not in cls._registry:
            with cls._lock:
                if provider not in cls._registry:
                    cls._registry[provider] = CircuitBreaker(
                        provider=provider,
                        failure_threshold=Config.CB_FAILURE_THRESHOLD,
                        recovery_timeout=Config.CB_RECOVERY_TIMEOUT,
                        half_open_max_calls=Config.CB_HALF_OPEN_MAX_CALLS,
                    )
        return cls._registry[provider]

    @classmethod
    def snapshot(cls) -> Dict[str, dict]:
        """Return a JSON-serialisable snapshot of all circuit breaker states."""
        result = {}
        for name, cb in cls._registry.items():
            result[name] = {
                "state":           cb.state.value,
                "failure_count":   cb._failure_count,
                "total_calls":     cb._stats.total_calls,
                "success_calls":   cb._stats.success_calls,
                "failure_calls":   cb._stats.failure_calls,
            }
        return result

    @classmethod
    def initialize_defaults(cls) -> None:
        """Pre-create circuit breakers for all known providers."""
        for provider in cls._PROVIDERS:
            cls.get(provider)


def get_circuit_breaker(provider: str) -> CircuitBreaker:
    """Convenience function — returns the circuit breaker for a provider."""
    return CircuitBreakerRegistry.get(provider)
