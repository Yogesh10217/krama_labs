"""
app/observability/metrics.py — Phase 11 Prometheus Metrics

Standardized metric labels (per approved spec):
  method, route, stage, provider, document_type, status, organization

Metric families:
  Counters:   http_requests_total, jobs_total, jobs_failed_total,
              jobs_cancelled_total, retry_count_total, auto_approvals_total,
              manual_reviews_total, provider_failures_total,
              circuit_breaker_transitions_total
  Histograms: http_request_duration_seconds, job_duration_seconds,
              stage_duration_seconds, provider_request_duration_seconds
  Gauges:     queue_size, worker_utilization, circuit_breaker_state

All metrics are namespaced under Config.PROMETHEUS_NAMESPACE (default: "krama").

Business services are NEVER aware of this module.
"""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from typing import Callable, Generator, Optional

try:
    from prometheus_client import (  # type: ignore
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
        CONTENT_TYPE_LATEST,
        REGISTRY,
    )
    _HAS_PROMETHEUS = True
except ImportError:
    _HAS_PROMETHEUS = False

from app.core.config import Config


# ---------------------------------------------------------------------------
# Histogram bucket presets
# ---------------------------------------------------------------------------

_HTTP_BUCKETS     = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
_JOB_BUCKETS      = [1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0]
_STAGE_BUCKETS    = [0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
_PROVIDER_BUCKETS = [0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]


class _NoOpMetric:
    """Placeholder when prometheus_client is not installed."""
    def labels(self, **kwargs):  return self
    def inc(self, *args, **kwargs): pass
    def dec(self, *args, **kwargs): pass
    def set(self, *args, **kwargs): pass
    def observe(self, *args, **kwargs): pass
    def time(self): return _NoOpContext()


class _NoOpContext:
    def __enter__(self): return self
    def __exit__(self, *a): pass


class KramaMetrics:
    """
    Singleton registry of all Phase 11 Prometheus metrics.

    Access via get_metrics_registry() — do not instantiate directly.
    """

    _instance: Optional[KramaMetrics] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        ns = Config.PROMETHEUS_NAMESPACE

        if not _HAS_PROMETHEUS:
            # Provide no-op stubs so business code never crashes
            self.http_requests_total               = _NoOpMetric()
            self.http_request_duration_seconds     = _NoOpMetric()
            self.jobs_total                        = _NoOpMetric()
            self.jobs_failed_total                 = _NoOpMetric()
            self.jobs_cancelled_total              = _NoOpMetric()
            self.retry_count_total                 = _NoOpMetric()
            self.auto_approvals_total              = _NoOpMetric()
            self.manual_reviews_total              = _NoOpMetric()
            self.provider_failures_total           = _NoOpMetric()
            self.provider_request_duration_seconds = _NoOpMetric()
            self.job_duration_seconds              = _NoOpMetric()
            self.stage_duration_seconds            = _NoOpMetric()
            self.queue_size                        = _NoOpMetric()
            self.worker_utilization                = _NoOpMetric()
            self.circuit_breaker_state             = _NoOpMetric()
            self.circuit_breaker_transitions_total = _NoOpMetric()
            self.circuit_breaker_success_total     = _NoOpMetric()
            self.circuit_breaker_failure_total     = _NoOpMetric()
            return

        # ── HTTP metrics ──────────────────────────────────────────────────
        self.http_requests_total = Counter(
            f"{ns}_http_requests_total",
            "Total HTTP requests by method, route, status, and organization.",
            ["method", "route", "status", "organization"],
        )

        self.http_request_duration_seconds = Histogram(
            f"{ns}_http_request_duration_seconds",
            "HTTP request latency in seconds.",
            ["method", "route", "status"],
            buckets=_HTTP_BUCKETS,
        )

        # ── Job metrics ───────────────────────────────────────────────────
        self.jobs_total = Counter(
            f"{ns}_jobs_total",
            "Total jobs submitted by organization and document type.",
            ["organization", "document_type"],
        )

        self.jobs_failed_total = Counter(
            f"{ns}_jobs_failed_total",
            "Total failed jobs by organization and stage.",
            ["organization", "stage"],
        )

        self.jobs_cancelled_total = Counter(
            f"{ns}_jobs_cancelled_total",
            "Total cancelled jobs.",
            ["organization"],
        )

        self.retry_count_total = Counter(
            f"{ns}_retry_count_total",
            "Total stage retry attempts.",
            ["stage", "organization"],
        )

        self.auto_approvals_total = Counter(
            f"{ns}_auto_approvals_total",
            "Documents auto-approved by the workflow stage.",
            ["organization", "document_type"],
        )

        self.manual_reviews_total = Counter(
            f"{ns}_manual_reviews_total",
            "Documents routed to manual review.",
            ["organization", "document_type"],
        )

        # ── Provider metrics ──────────────────────────────────────────────
        self.provider_failures_total = Counter(
            f"{ns}_provider_failures_total",
            "Provider call failures.",
            ["provider", "organization"],
        )

        self.provider_request_duration_seconds = Histogram(
            f"{ns}_provider_request_duration_seconds",
            "Provider request latency in seconds.",
            ["provider", "organization"],
            buckets=_PROVIDER_BUCKETS,
        )

        # ── Pipeline metrics ──────────────────────────────────────────────
        self.job_duration_seconds = Histogram(
            f"{ns}_job_duration_seconds",
            "End-to-end job execution time in seconds.",
            ["organization", "document_type", "status"],
            buckets=_JOB_BUCKETS,
        )

        self.stage_duration_seconds = Histogram(
            f"{ns}_stage_duration_seconds",
            "Individual pipeline stage execution time in seconds.",
            ["stage", "organization", "status"],
            buckets=_STAGE_BUCKETS,
        )

        # ── Queue and worker gauges ───────────────────────────────────────
        self.queue_size = Gauge(
            f"{ns}_queue_size",
            "Current approximate number of messages in the job queue.",
        )

        self.worker_utilization = Gauge(
            f"{ns}_worker_utilization",
            "Ratio of active workers to total worker capacity (0.0–1.0).",
        )

        # ── Circuit breaker metrics ───────────────────────────────────────
        # State gauge: 0=CLOSED, 1=OPEN, 2=HALF_OPEN
        self.circuit_breaker_state = Gauge(
            f"{ns}_circuit_breaker_state",
            "Current circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN).",
            ["provider"],
        )

        self.circuit_breaker_transitions_total = Counter(
            f"{ns}_circuit_breaker_transitions_total",
            "Total circuit breaker state transitions.",
            ["provider", "from_state", "to_state"],
        )

        self.circuit_breaker_success_total = Counter(
            f"{ns}_circuit_breaker_success_total",
            "Total successful calls recorded by circuit breakers.",
            ["provider"],
        )

        self.circuit_breaker_failure_total = Counter(
            f"{ns}_circuit_breaker_failure_total",
            "Total failed calls recorded by circuit breakers.",
            ["provider"],
        )


def get_metrics_registry() -> KramaMetrics:
    """Return the singleton KramaMetrics instance (thread-safe)."""
    if KramaMetrics._instance is None:
        with KramaMetrics._lock:
            if KramaMetrics._instance is None:
                KramaMetrics._instance = KramaMetrics()
    return KramaMetrics._instance


# ---------------------------------------------------------------------------
# Convenience context manager for stage/provider timing
# ---------------------------------------------------------------------------

@contextmanager
def track_duration(
    histogram_labels_fn: Callable[[], dict],
    histogram_attr: str = "stage_duration_seconds",
) -> Generator[None, None, None]:
    """
    Context manager that records duration to the named histogram.

    Usage:
        metrics = get_metrics_registry()
        with track_duration(lambda: {"stage": "ocr", "organization": org_id, "status": "success"}):
            do_ocr()
    """
    start = time.perf_counter()
    status = "success"
    try:
        yield
    except Exception:
        status = "error"
        raise
    finally:
        elapsed = time.perf_counter() - start
        labels = histogram_labels_fn()
        labels["status"] = status
        m = get_metrics_registry()
        hist = getattr(m, histogram_attr, None)
        if hist:
            try:
                hist.labels(**labels).observe(elapsed)
            except Exception:
                pass  # Never let metrics crash business code


def get_prometheus_output() -> tuple[str, str]:
    """
    Generate Prometheus text format output.

    Returns: (content, content_type)
    """
    if not _HAS_PROMETHEUS:
        return "# prometheus_client not installed\n", "text/plain"
    return generate_latest(REGISTRY).decode(), CONTENT_TYPE_LATEST
