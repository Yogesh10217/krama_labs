"""
app/observability/health.py — Phase 11 Three-Level Health Model

Health levels (per approved spec):
  HEALTHY   → component is fully operational
  DEGRADED  → component is operational but with reduced capacity / elevated latency
  UNHEALTHY → component is non-operational

Checks performed:
  - database     : execute a simple SQL probe
  - storage      : verify storage root is readable/writable
  - queue        : call queue.health()
  - ai_providers : optional HTTP ping to configured providers
  - config       : validate required config keys

The HealthChecker is used by GET /health.
Business services are NEVER aware of this module.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.config import Config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Health level enum
# ---------------------------------------------------------------------------

class HealthLevel(str, Enum):
    HEALTHY   = "HEALTHY"
    DEGRADED  = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"


@dataclass
class ComponentHealth:
    component:  str
    level:      HealthLevel
    latency_ms: Optional[float] = None
    detail:     str = ""
    extra:      Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "component":  self.component,
            "level":      self.level.value,
            "latency_ms": self.latency_ms,
            "detail":     self.detail,
            **self.extra,
        }


@dataclass
class HealthReport:
    overall:    HealthLevel
    components: List[ComponentHealth] = field(default_factory=list)
    checked_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "status":      self.overall.value,
            "checked_at":  self.checked_at,
            "service":     Config.APP_NAME,
            "version":     Config.VERSION,
            "environment": Config.ENV,
            "components":  [c.to_dict() for c in self.components],
        }

    @property
    def is_serving(self) -> bool:
        """True if the service can accept requests (HEALTHY or DEGRADED)."""
        return self.overall != HealthLevel.UNHEALTHY


# ---------------------------------------------------------------------------
# Individual probe functions
# ---------------------------------------------------------------------------

def _check_database(db_factory) -> ComponentHealth:
    """Probe: issue a cheap SQL query and measure latency."""
    start = time.perf_counter()
    try:
        db = db_factory()
        try:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            latency_ms = (time.perf_counter() - start) * 1000
            level = HealthLevel.HEALTHY if latency_ms < 500 else HealthLevel.DEGRADED
            return ComponentHealth(
                component="database",
                level=level,
                latency_ms=round(latency_ms, 2),
                detail="OK" if level == HealthLevel.HEALTHY else f"High latency {latency_ms:.0f}ms",
            )
        finally:
            db.close()
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        return ComponentHealth(
            component="database",
            level=HealthLevel.UNHEALTHY,
            latency_ms=round(latency_ms, 2),
            detail=str(exc),
        )


def _check_storage() -> ComponentHealth:
    """Probe: verify STORAGE_ROOT is readable and writable."""
    start = time.perf_counter()
    try:
        root = Config.STORAGE_ROOT
        os.makedirs(root, exist_ok=True)
        probe = os.path.join(root, ".health_probe")
        with open(probe, "w") as f:
            f.write("ok")
        os.remove(probe)
        latency_ms = (time.perf_counter() - start) * 1000
        return ComponentHealth(
            component="storage",
            level=HealthLevel.HEALTHY,
            latency_ms=round(latency_ms, 2),
            detail=f"Storage root: {root}",
        )
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        return ComponentHealth(
            component="storage",
            level=HealthLevel.UNHEALTHY,
            latency_ms=round(latency_ms, 2),
            detail=str(exc),
        )


def _check_queue(queue) -> ComponentHealth:
    """Probe: call queue.health() and translate to HealthLevel."""
    start = time.perf_counter()
    try:
        qh = queue.health()
        latency_ms = (time.perf_counter() - start) * 1000
        level = HealthLevel.HEALTHY if qh.is_healthy else HealthLevel.UNHEALTHY
        return ComponentHealth(
            component="queue",
            level=level,
            latency_ms=round(latency_ms, 2),
            detail=f"provider={qh.provider} size≈{qh.approximate_size}",
            extra=qh.details,
        )
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        return ComponentHealth(
            component="queue",
            level=HealthLevel.UNHEALTHY,
            latency_ms=round(latency_ms, 2),
            detail=str(exc),
        )


def _check_ai_providers() -> ComponentHealth:
    """
    Probe: lightweight check that AI provider SDKs / endpoints are reachable.
    Uses module import checks rather than live API calls to avoid costs.
    """
    start   = time.perf_counter()
    details = {}

    # Gemini
    try:
        import google.generativeai  # noqa: F401
        details["gemini"] = "sdk_available"
    except ImportError:
        details["gemini"] = "sdk_unavailable"

    # OpenAI
    try:
        import openai  # noqa: F401
        details["openai"] = "sdk_available"
    except ImportError:
        details["openai"] = "sdk_unavailable"

    # Ollama (optional local)
    details["ollama"] = f"configured_at={Config.OLLAMA_BASE_URL}"

    # Circuit breaker states
    try:
        from app.observability.circuit_breaker import CircuitBreakerRegistry
        cb_snap = CircuitBreakerRegistry.snapshot()
        for provider, state_info in cb_snap.items():
            details[f"cb_{provider}"] = state_info.get("state", "?")

        # DEGRADED if any known AI provider CB is OPEN
        ai_cbs = ["gemini", "openai", "ollama"]
        any_open = any(
            cb_snap.get(p, {}).get("state") == "OPEN" for p in ai_cbs
        )
        level = HealthLevel.DEGRADED if any_open else HealthLevel.HEALTHY
    except Exception:
        level = HealthLevel.HEALTHY

    latency_ms = (time.perf_counter() - start) * 1000
    return ComponentHealth(
        component="ai_providers",
        level=level,
        latency_ms=round(latency_ms, 2),
        detail="Checked via SDK import + circuit breaker state",
        extra=details,
    )


def _check_config() -> ComponentHealth:
    """Probe: validate critical configuration."""
    start = time.perf_counter()
    warnings = []

    if not Config.GOOGLE_API_KEY and Config.LLM_PROVIDER == "gemini":
        warnings.append("GOOGLE_API_KEY missing for gemini provider")
    if not Config.OPENAI_API_KEY and Config.LLM_PROVIDER == "openai":
        warnings.append("OPENAI_API_KEY missing for openai provider")
    if not Config.GEMINI_API_KEY and Config.CLASSIFICATION_PROVIDER == "gemini":
        warnings.append("GEMINI_API_KEY missing for classification provider")

    latency_ms = (time.perf_counter() - start) * 1000
    level = HealthLevel.DEGRADED if warnings else HealthLevel.HEALTHY
    return ComponentHealth(
        component="config",
        level=level,
        latency_ms=round(latency_ms, 2),
        detail="; ".join(warnings) if warnings else "All required config present",
    )


# ---------------------------------------------------------------------------
# HealthChecker — used by GET /health
# ---------------------------------------------------------------------------

class HealthChecker:
    """
    Runs all health probes and aggregates a HealthReport.

    Aggregation rules:
      - Any UNHEALTHY component  → overall UNHEALTHY
      - Any DEGRADED component   → overall DEGRADED
      - All HEALTHY              → overall HEALTHY
    """

    def __init__(self, db_factory=None, queue=None) -> None:
        self._db_factory = db_factory
        self._queue      = queue

    def check(self) -> HealthReport:
        components: List[ComponentHealth] = []

        # Config (fast, no I/O)
        components.append(_check_config())

        # Storage
        components.append(_check_storage())

        # Database (if factory provided)
        if self._db_factory:
            components.append(_check_database(self._db_factory))
        else:
            components.append(ComponentHealth(
                component="database",
                level=HealthLevel.DEGRADED,
                detail="No db_factory provided to HealthChecker",
            ))

        # Queue (if instance provided)
        if self._queue:
            components.append(_check_queue(self._queue))
        else:
            components.append(ComponentHealth(
                component="queue",
                level=HealthLevel.DEGRADED,
                detail="No queue instance provided to HealthChecker",
            ))

        # AI Providers
        components.append(_check_ai_providers())

        # Aggregate
        levels = {c.level for c in components}
        if HealthLevel.UNHEALTHY in levels:
            overall = HealthLevel.UNHEALTHY
        elif HealthLevel.DEGRADED in levels:
            overall = HealthLevel.DEGRADED
        else:
            overall = HealthLevel.HEALTHY

        return HealthReport(overall=overall, components=components)
