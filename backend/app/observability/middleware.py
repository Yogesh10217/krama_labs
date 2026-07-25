"""
app/observability/middleware.py — Phase 11 Middleware Stack

Execution order (per approved spec):
  Correlation → Logging → Rate Limit → Metrics → Timing → Route → Exception Handler

Each middleware handles exactly one concern.

Middleware:
  1. CorrelationIdMiddleware   — extract/generate X-Correlation-ID
  2. RequestLoggingMiddleware  — structured access logs
  3. RateLimitMiddleware       — per-key sliding-window rate limit
  4. MetricsMiddleware         — Prometheus counter + histogram
  5. RequestTimingMiddleware   — slow-request threshold warnings

Rate limit key abstraction (future-compatible):
  The _extract_rate_key() function supports organization, API key,
  user, or IP-based keying. Currently uses X-Organization-ID header
  with IP fallback.
"""

from __future__ import annotations

import logging
import time
import threading
import uuid
from collections import defaultdict, deque
from typing import Callable, Deque, Dict, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import Config
from app.observability.logging import bind_context, clear_context

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Correlation ID Middleware
# ---------------------------------------------------------------------------

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Layer 1: Extract or generate a correlation ID and propagate it.

    Priority (highest → lowest):
      1. X-Correlation-ID header (upstream gateway / existing trace)
      2. X-Request-ID header (legacy clients)
      3. Generated UUID

    The ID is:
      - Stored in the log context so every subsequent log record carries it.
      - Returned in X-Correlation-ID response header.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Request-ID")
            or str(uuid.uuid4())
        )

        # Propagate to log context
        token = bind_context(correlation_id=correlation_id)
        try:
            response: Response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        finally:
            clear_context(token)


# ---------------------------------------------------------------------------
# 2. Request Logging Middleware
# ---------------------------------------------------------------------------

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Layer 2: Emit a structured JSON access log for every request.

    Logs: method, path, status, duration_ms, correlation_id (via context).
    Does NOT log request bodies to avoid PII leakage.
    """

    # Routes whose access logs we suppress (e.g. health probes are noisy)
    _SUPPRESS_ROUTES = frozenset(["/api/live", "/api/v1/live", "/api/ready", "/api/v1/ready"])

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response: Optional[Response] = None
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000

            if request.url.path not in self._SUPPRESS_ROUTES:
                token = bind_context(
                    event="http_request",
                    duration_ms=round(duration_ms, 2),
                )
                try:
                    logger.info(
                        "%s %s → %d (%.1fms)",
                        request.method,
                        request.url.path,
                        status_code,
                        duration_ms,
                    )
                finally:
                    clear_context(token)


# ---------------------------------------------------------------------------
# 3. Rate Limit Middleware
# ---------------------------------------------------------------------------

class _SlidingWindowCounter:
    """Thread-safe sliding-window request counter per key."""

    def __init__(self, window_seconds: int, max_requests: int, burst: int) -> None:
        self._window     = window_seconds
        self._max        = max_requests
        self._burst      = burst
        self._buckets:   Dict[str, Deque[float]] = defaultdict(deque)
        self._lock       = threading.Lock()

    def is_allowed(self, key: str) -> tuple[bool, int]:
        """
        Returns (allowed, remaining).
        allowed=False when the key has exceeded max_requests + burst
        within the sliding window.
        """
        now    = time.monotonic()
        cutoff = now - self._window
        limit  = self._max + self._burst

        with self._lock:
            bucket = self._buckets[key]
            # Remove timestamps outside the window
            while bucket and bucket[0] < cutoff:
                bucket.popleft()

            count = len(bucket)
            if count >= limit:
                remaining = 0
                return False, remaining

            bucket.append(now)
            remaining = max(0, limit - count - 1)
            return True, remaining


def _extract_rate_key(request: Request) -> str:
    """
    Rate-limit key abstraction.

    Keying priority (most specific → least specific):
      1. X-Organization-ID header     — per-organization rate limit
      2. X-API-Key header prefix      — per API key (future)
      3. X-Forwarded-For / client IP  — IP-based fallback

    Future implementations can add JWT-derived user IDs by extending here.
    """
    org = request.headers.get("X-Organization-ID")
    if org:
        return f"org:{org}"

    api_key = request.headers.get("X-API-Key")
    if api_key:
        # Use only first 8 chars as key prefix (avoids storing full secret)
        return f"apikey:{api_key[:8]}"

    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"

    client_host = (request.client.host if request.client else None) or "unknown"
    return f"ip:{client_host}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Layer 3: Sliding-window rate limiting.

    Responds HTTP 429 with Retry-After header when limit exceeded.
    Health/metrics endpoints are exempt.

    The _extract_rate_key() function supports future keying strategies:
    organization, API key, user, or IP.
    """

    _EXEMPT_PATHS = frozenset([
        "/api/live", "/api/v1/live",
        "/api/ready", "/api/v1/ready",
        "/api/health", "/api/v1/health",
        "/api/metrics", "/api/v1/metrics",
    ])

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._counter = _SlidingWindowCounter(
            window_seconds=Config.RATE_LIMIT_WINDOW,
            max_requests=Config.RATE_LIMIT_REQUESTS,
            burst=Config.RATE_LIMIT_BURST,
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self._EXEMPT_PATHS:
            return await call_next(request)

        key = _extract_rate_key(request)
        allowed, remaining = self._counter.is_allowed(key)

        if not allowed:
            from starlette.responses import JSONResponse
            logger.warning(
                "Rate limit exceeded for key=%s path=%s",
                key, request.url.path,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please retry after the window expires.",
                    "retry_after_seconds": Config.RATE_LIMIT_WINDOW,
                },
                headers={
                    "X-RateLimit-Limit":     str(Config.RATE_LIMIT_REQUESTS),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After":           str(Config.RATE_LIMIT_WINDOW),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"]     = str(Config.RATE_LIMIT_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


# ---------------------------------------------------------------------------
# 4. Metrics Middleware
# ---------------------------------------------------------------------------

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Layer 4: Record Prometheus HTTP metrics.

    Records:
      - krama_http_requests_total (method, route, status, organization)
      - krama_http_request_duration_seconds (method, route, status)

    Route normalization: removes path parameters (/documents/abc123 → /documents/{id})
    so cardinality stays bounded.
    """

    _ROUTE_PATTERNS = [
        # Add known variable-segment routes for normalization
        ("/documents/", "/documents/{id}"),
        ("/claims/",    "/claims/{id}"),
        ("/jobs/",      "/jobs/{id}"),
        ("/pages/",     "/pages/{id}"),
        ("/organizations/", "/organizations/{id}"),
    ]

    def _normalize_route(self, path: str) -> str:
        for prefix, template in self._ROUTE_PATTERNS:
            if path.startswith(prefix) and path != prefix.rstrip("/"):
                return template
        return path

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not Config.ENABLE_METRICS:
            return await call_next(request)

        start = time.perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.perf_counter() - start
            route    = self._normalize_route(request.url.path)
            method   = request.method
            status   = str(status_code)
            org      = request.headers.get("X-Organization-ID", "unknown")

            try:
                from app.observability.metrics import get_metrics_registry
                m = get_metrics_registry()
                m.http_requests_total.labels(
                    method=method, route=route, status=status, organization=org
                ).inc()
                m.http_request_duration_seconds.labels(
                    method=method, route=route, status=status
                ).observe(duration)
            except Exception:
                pass  # Metrics must NEVER crash the application


# ---------------------------------------------------------------------------
# 5. Request Timing Middleware (slow-request warnings)
# ---------------------------------------------------------------------------

class RequestTimingMiddleware(BaseHTTPMiddleware):
    """
    Layer 5: Emit a WARNING log when a request exceeds SLOW_REQUEST_THRESHOLD_MS.

    This is a non-invasive observability aid — it does not alter responses,
    retries, or timeouts. Pure logging side-effect only.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            if duration_ms > Config.SLOW_REQUEST_THRESHOLD_MS:
                logger.warning(
                    "SLOW REQUEST: %s %s took %.1fms (threshold=%dms)",
                    request.method,
                    request.url.path,
                    duration_ms,
                    Config.SLOW_REQUEST_THRESHOLD_MS,
                )
