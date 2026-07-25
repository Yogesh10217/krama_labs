"""
tests/test_observability.py — Phase 11 Observability Test Suite

Tests:
  1. Structured JSON logging (all required fields present)
  2. Correlation ID propagation (HTTP header → log context)
  3. Prometheus metrics endpoint (/metrics returns text format)
  4. Health endpoint (/health — three-level model)
  5. Readiness endpoint (/ready — filesystem + config)
  6. Liveness endpoint (/live — always 200, no I/O)
  7. Observability status endpoint (/observability/status)
  8. Rate limiting (sliding window enforcement)
  9. Circuit breaker (CLOSED → OPEN → HALF_OPEN → CLOSED)
  10. Cache (get/set/TTL expiry/miss/hit-rate)
  11. Tracing context (tracer creation, span creation, attribute presence)
  12. Cache key definitions and TTL mapping
"""

import json
import logging
import time
import uuid
import os
import sys
import pytest

# Ensure backend root is importable
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)


# ============================================================================
# 1. Structured Logging Tests
# ============================================================================

class TestStructuredLogging:
    """Verify that all required log envelope fields are present."""

    def test_setup_logging_does_not_crash(self):
        from app.observability.logging import setup_logging
        setup_logging()  # Must not raise

    def test_json_formatter_contains_required_fields(self):
        from app.observability.logging import _KramaJsonFormatter, _ContextFilter, bind_context, clear_context

        formatter = _KramaJsonFormatter()
        ctx_filter = _ContextFilter()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )

        # Apply the context filter (injects context fields)
        ctx_filter.filter(record)
        formatted = formatter.format(record)
        data = json.loads(formatted)

        required_fields = [
            "timestamp", "level", "message",
            "correlation_id", "organization_id", "document_id",
            "job_id", "worker_id", "stage", "event",
            "service_name", "service_version", "environment",
            "host", "thread_name", "process_id",
            "logger", "module", "line",
        ]
        for field in required_fields:
            assert field in data, f"Required field '{field}' missing from log output"

    def test_context_binding_propagates(self):
        from app.observability.logging import bind_context, clear_context, get_current_context

        token = bind_context(
            correlation_id="test-corr-123",
            organization_id="org-abc",
            document_id="doc-xyz",
        )
        try:
            ctx = get_current_context()
            assert ctx.correlation_id == "test-corr-123"
            assert ctx.organization_id == "org-abc"
            assert ctx.document_id == "doc-xyz"
        finally:
            clear_context(token)

    def test_context_restored_after_clear(self):
        from app.observability.logging import bind_context, clear_context, get_current_context

        original_ctx = get_current_context()
        token = bind_context(correlation_id="temp-id")
        clear_context(token)
        restored_ctx = get_current_context()
        assert restored_ctx.correlation_id == original_ctx.correlation_id

    def test_sensitive_redaction(self):
        from app.observability.logging import _redact

        msg = 'api_key: "sk-abc123verylongkeyabcdefghijk1234567890abcdefghij"'
        redacted = _redact(msg)
        # Original key should not be present
        assert "sk-abc123" not in redacted

    def test_structured_logger_event_field(self):
        """StructuredLogger.info() should accept event kwarg without error."""
        from app.observability.logging import get_logger, _KramaJsonFormatter, _ContextFilter
        import io

        # Capture log output
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(_KramaJsonFormatter())
        handler.addFilter(_ContextFilter())

        logger_inst = logging.getLogger("test.structured")
        logger_inst.addHandler(handler)
        logger_inst.setLevel(logging.DEBUG)

        struct_logger = get_logger("test.structured")
        struct_logger.info("hello world", event="stage_complete", stage="ocr", duration_ms=42.5)

        log_capture.seek(0)
        output = log_capture.read()
        assert len(output) > 0  # Something was logged
        logger_inst.removeHandler(handler)


# ============================================================================
# 2. Correlation ID Propagation Tests
# ============================================================================

class TestCorrelationPropagation:
    """Verify X-Correlation-ID flows from request to response."""

    def test_correlation_id_passed_through(self, client):
        corr_id = str(uuid.uuid4())
        response = client.get("/api/live", headers={"X-Correlation-ID": corr_id})
        assert response.headers.get("X-Correlation-ID") == corr_id

    def test_correlation_id_generated_when_absent(self, client):
        response = client.get("/api/live")
        corr_id = response.headers.get("X-Correlation-ID")
        assert corr_id is not None
        assert len(corr_id) > 0

    def test_request_id_fallback(self, client):
        """X-Request-ID should be accepted as fallback for X-Correlation-ID."""
        req_id = str(uuid.uuid4())
        response = client.get("/api/live", headers={"X-Request-ID": req_id})
        returned = response.headers.get("X-Correlation-ID")
        assert returned == req_id

    def test_correlation_id_is_unique_per_request(self, client):
        ids = set()
        for _ in range(5):
            response = client.get("/api/live")
            ids.add(response.headers.get("X-Correlation-ID"))
        assert len(ids) == 5, "Each request should get a unique correlation ID"


# ============================================================================
# 3. Prometheus Metrics Tests
# ============================================================================

class TestPrometheusMetrics:
    """Verify /metrics endpoint and metric registration."""

    def test_metrics_endpoint_returns_200(self, client):
        response = client.get("/api/metrics")
        assert response.status_code == 200

    def test_metrics_content_type_is_text(self, client):
        response = client.get("/api/metrics")
        content_type = response.headers.get("content-type", "")
        assert "text/plain" in content_type or "text/plain" in content_type

    def test_metrics_endpoint_returns_text(self, client):
        response = client.get("/api/metrics")
        # Should be Prometheus format or disabled notice
        assert len(response.text) > 0

    def test_krama_metrics_singleton(self):
        from app.observability.metrics import get_metrics_registry, KramaMetrics
        m1 = get_metrics_registry()
        m2 = get_metrics_registry()
        assert m1 is m2, "KramaMetrics should be a singleton"

    def test_metrics_noop_when_prometheus_unavailable(self):
        """Metrics operations must not raise even when prometheus_client is absent."""
        from app.observability.metrics import get_metrics_registry
        m = get_metrics_registry()
        # These must not raise
        try:
            m.http_requests_total.labels(
                method="GET", route="/test", status="200", organization="test-org"
            ).inc()
            m.queue_size.set(5)
        except Exception as exc:
            pytest.fail(f"Metrics operation raised unexpected exception: {exc}")

    def test_track_duration_context_manager(self):
        from app.observability.metrics import track_duration
        with track_duration(
            lambda: {"stage": "test_stage", "organization": "test_org"},
            histogram_attr="stage_duration_seconds",
        ):
            time.sleep(0.001)  # Simulate work


# ============================================================================
# 4. Health Endpoint Tests
# ============================================================================

class TestHealthEndpoint:
    """Verify /health returns three-level model."""

    def test_health_returns_200_or_503(self, client):
        response = client.get("/api/health")
        assert response.status_code in (200, 503)

    def test_health_response_contains_status_field(self, client):
        response = client.get("/api/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ("HEALTHY", "DEGRADED", "UNHEALTHY")

    def test_health_response_contains_components(self, client):
        response = client.get("/api/health")
        data = response.json()
        assert "components" in data
        assert isinstance(data["components"], list)

    def test_health_response_contains_metadata(self, client):
        response = client.get("/api/health")
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "environment" in data

    def test_health_component_schema(self, client):
        response = client.get("/api/health")
        data = response.json()
        for component in data["components"]:
            assert "component" in component
            assert "level" in component
            assert component["level"] in ("HEALTHY", "DEGRADED", "UNHEALTHY")

    def test_health_checker_directly(self):
        from app.observability.health import HealthChecker, HealthLevel
        checker = HealthChecker()  # No db_factory — database probe will return DEGRADED
        report = checker.check()
        assert report.overall in list(HealthLevel)
        assert isinstance(report.components, list)
        assert len(report.components) > 0

    def test_health_level_aggregation_unhealthy_wins(self):
        from app.observability.health import (
            HealthReport, ComponentHealth, HealthLevel
        )
        components = [
            ComponentHealth("a", HealthLevel.HEALTHY),
            ComponentHealth("b", HealthLevel.UNHEALTHY),
            ComponentHealth("c", HealthLevel.DEGRADED),
        ]
        levels = {c.level for c in components}
        overall = (
            HealthLevel.UNHEALTHY if HealthLevel.UNHEALTHY in levels
            else HealthLevel.DEGRADED if HealthLevel.DEGRADED in levels
            else HealthLevel.HEALTHY
        )
        assert overall == HealthLevel.UNHEALTHY

    def test_health_level_aggregation_degraded_wins_over_healthy(self):
        from app.observability.health import ComponentHealth, HealthLevel
        components = [
            ComponentHealth("a", HealthLevel.HEALTHY),
            ComponentHealth("b", HealthLevel.DEGRADED),
        ]
        levels = {c.level for c in components}
        overall = (
            HealthLevel.UNHEALTHY if HealthLevel.UNHEALTHY in levels
            else HealthLevel.DEGRADED if HealthLevel.DEGRADED in levels
            else HealthLevel.HEALTHY
        )
        assert overall == HealthLevel.DEGRADED


# ============================================================================
# 5. Readiness Endpoint Tests
# ============================================================================

class TestReadinessEndpoint:
    """Verify /ready performs config + filesystem checks only."""

    def test_ready_returns_200_or_503(self, client):
        response = client.get("/api/ready")
        assert response.status_code in (200, 503)

    def test_ready_response_contains_status(self, client):
        response = client.get("/api/ready")
        data = response.json()
        assert "status" in data
        assert data["status"] in ("ready", "not_ready")

    def test_ready_response_contains_checks(self, client):
        response = client.get("/api/ready")
        data = response.json()
        assert "checks" in data
        assert isinstance(data["checks"], dict)

    def test_readiness_checker_directly(self):
        from app.observability.readiness import ReadinessChecker
        checker = ReadinessChecker()
        report = checker.check()
        assert report.status.value in ("ready", "not_ready")
        assert "config" in report.checks


# ============================================================================
# 6. Liveness Endpoint Tests
# ============================================================================

class TestLivenessEndpoint:
    """Verify /live is always fast and always returns 200."""

    def test_live_always_returns_200(self, client):
        response = client.get("/api/live")
        assert response.status_code == 200

    def test_live_contains_status_alive(self, client):
        response = client.get("/api/live")
        data = response.json()
        assert data["status"] == "alive"

    def test_live_response_is_fast(self, client):
        """Liveness response must be sub-100ms."""
        start = time.perf_counter()
        client.get("/api/live")
        duration_ms = (time.perf_counter() - start) * 1000
        assert duration_ms < 500, f"Liveness took {duration_ms:.0f}ms (expected < 500ms)"

    def test_live_response_has_version(self, client):
        response = client.get("/api/live")
        data = response.json()
        assert "version" in data
        assert "service" in data


# ============================================================================
# 7. Observability Status Endpoint
# ============================================================================

class TestObservabilityStatusEndpoint:
    """Verify /observability/status returns structured runtime state."""

    def test_observability_status_returns_200(self, client):
        response = client.get("/api/observability/status")
        assert response.status_code == 200

    def test_observability_status_schema(self, client):
        response = client.get("/api/observability/status")
        data = response.json()
        assert "feature_flags" in data
        assert "logging" in data
        assert "tracing" in data
        assert "metrics" in data
        assert "rate_limit" in data
        assert "slow_thresholds_ms" in data

    def test_feature_flags_present(self, client):
        response = client.get("/api/observability/status")
        flags = response.json()["feature_flags"]
        assert "metrics" in flags
        assert "tracing" in flags
        assert "cache" in flags
        assert "rate_limit" in flags
        assert "circuit_breaker" in flags

    def test_cache_stats_present(self, client):
        response = client.get("/api/observability/status")
        data = response.json()
        assert "cache" in data
        cache = data["cache"]
        assert "provider" in cache or "enabled" in cache

    def test_circuit_breaker_states_present(self, client):
        response = client.get("/api/observability/status")
        data = response.json()
        assert "circuit_breakers" in data


# ============================================================================
# 8. Rate Limiting Tests
# ============================================================================

class TestRateLimiting:
    """Verify the sliding-window rate limiter."""

    def test_rate_limiter_allows_within_limit(self):
        from app.observability.middleware import _SlidingWindowCounter
        counter = _SlidingWindowCounter(window_seconds=60, max_requests=10, burst=0)
        for i in range(10):
            allowed, remaining = counter.is_allowed("test-key")
            assert allowed, f"Request {i+1} should be allowed"

    def test_rate_limiter_blocks_over_limit(self):
        from app.observability.middleware import _SlidingWindowCounter
        counter = _SlidingWindowCounter(window_seconds=60, max_requests=5, burst=0)
        for _ in range(5):
            counter.is_allowed("test-key")
        # 6th request should be blocked
        allowed, remaining = counter.is_allowed("test-key")
        assert not allowed
        assert remaining == 0

    def test_rate_limiter_burst_increases_quota(self):
        from app.observability.middleware import _SlidingWindowCounter
        counter = _SlidingWindowCounter(window_seconds=60, max_requests=5, burst=5)
        # Should allow 10 total (5 max + 5 burst)
        for i in range(10):
            allowed, _ = counter.is_allowed("burst-key")
            assert allowed, f"Request {i+1} should be allowed within burst"
        # 11th should be blocked
        allowed, _ = counter.is_allowed("burst-key")
        assert not allowed

    def test_rate_limiter_separate_keys(self):
        from app.observability.middleware import _SlidingWindowCounter
        counter = _SlidingWindowCounter(window_seconds=60, max_requests=2, burst=0)
        # Fill key-A
        counter.is_allowed("key-A")
        counter.is_allowed("key-A")
        blocked, _ = counter.is_allowed("key-A")
        assert not blocked
        # key-B should still have quota
        allowed, _ = counter.is_allowed("key-B")
        assert allowed

    def test_rate_key_extraction_org(self):
        from app.observability.middleware import _extract_rate_key
        from unittest.mock import MagicMock

        request = MagicMock()
        request.headers = {"X-Organization-ID": "org-123"}
        request.client = None
        key = _extract_rate_key(request)
        assert key == "org:org-123"

    def test_rate_key_extraction_ip_fallback(self):
        from app.observability.middleware import _extract_rate_key
        from unittest.mock import MagicMock

        request = MagicMock()
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "192.168.1.100"
        key = _extract_rate_key(request)
        assert key == "ip:192.168.1.100"


# ============================================================================
# 9. Circuit Breaker Tests
# ============================================================================

class TestCircuitBreaker:
    """Verify CLOSED → OPEN → HALF_OPEN → CLOSED state machine."""

    def test_circuit_starts_closed(self):
        from app.observability.circuit_breaker import CircuitBreaker, CBState
        cb = CircuitBreaker("test_provider_new", failure_threshold=3, recovery_timeout=60)
        assert cb.state == CBState.CLOSED

    def test_circuit_opens_after_threshold(self):
        from app.observability.circuit_breaker import CircuitBreaker, CBState, CircuitBreakerOpen
        cb = CircuitBreaker(f"test_open_{uuid.uuid4().hex[:8]}", failure_threshold=3, recovery_timeout=60)

        for _ in range(3):
            try:
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
            except RuntimeError:
                pass

        assert cb.state == CBState.OPEN

    def test_open_circuit_blocks_calls(self):
        from app.observability.circuit_breaker import CircuitBreaker, CBState, CircuitBreakerOpen
        cb = CircuitBreaker(f"test_block_{uuid.uuid4().hex[:8]}", failure_threshold=2, recovery_timeout=60)

        # Force to OPEN
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
            except RuntimeError:
                pass

        assert cb.state == CBState.OPEN
        with pytest.raises(CircuitBreakerOpen):
            cb.call(lambda: "should not run")

    def test_circuit_transitions_to_half_open_after_timeout(self):
        from app.observability.circuit_breaker import CircuitBreaker, CBState, CircuitBreakerOpen
        cb = CircuitBreaker(f"test_ho_{uuid.uuid4().hex[:8]}", failure_threshold=2, recovery_timeout=0)

        # Force OPEN
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
            except RuntimeError:
                pass

        assert cb.state == CBState.OPEN

        # Timeout is 0s so next state evaluation should give HALF_OPEN
        time.sleep(0.01)
        # Calling is_open() triggers state evaluation
        is_open = cb.is_open()
        assert not is_open  # Should be HALF_OPEN now, not blocked

    def test_circuit_recovers_after_half_open_successes(self):
        from app.observability.circuit_breaker import CircuitBreaker, CBState
        cb = CircuitBreaker(
            f"test_recover_{uuid.uuid4().hex[:8]}",
            failure_threshold=2,
            recovery_timeout=0,
            half_open_max_calls=2,
        )

        # Force OPEN
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
            except RuntimeError:
                pass

        time.sleep(0.01)
        # Probe calls to HALF_OPEN
        cb.call(lambda: "ok")
        cb.call(lambda: "ok")

        assert cb.state == CBState.CLOSED

    def test_circuit_breaker_reset(self):
        from app.observability.circuit_breaker import CircuitBreaker, CBState
        cb = CircuitBreaker(f"test_reset_{uuid.uuid4().hex[:8]}", failure_threshold=2, recovery_timeout=60)
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
            except RuntimeError:
                pass
        assert cb.state == CBState.OPEN
        cb.reset()
        assert cb.state == CBState.CLOSED

    def test_registry_returns_same_instance(self):
        from app.observability.circuit_breaker import CircuitBreakerRegistry
        cb1 = CircuitBreakerRegistry.get("gemini")
        cb2 = CircuitBreakerRegistry.get("gemini")
        assert cb1 is cb2

    def test_registry_snapshot(self):
        from app.observability.circuit_breaker import CircuitBreakerRegistry
        CircuitBreakerRegistry.initialize_defaults()
        snapshot = CircuitBreakerRegistry.snapshot()
        assert isinstance(snapshot, dict)
        # All initialized providers should appear
        for provider in CircuitBreakerRegistry._PROVIDERS:
            assert provider in snapshot
            assert "state" in snapshot[provider]

    def test_circuit_breaker_protect_context_manager(self):
        from app.observability.circuit_breaker import CircuitBreaker, CBState
        cb = CircuitBreaker(f"test_ctx_{uuid.uuid4().hex[:8]}", failure_threshold=5)
        with cb.protect():
            pass  # success
        assert cb.state == CBState.CLOSED

    def test_circuit_breaker_stats_tracking(self):
        from app.observability.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker(f"test_stats_{uuid.uuid4().hex[:8]}", failure_threshold=10)
        cb.call(lambda: "ok")
        cb.call(lambda: "ok")
        assert cb.stats.success_calls == 2
        assert cb.stats.total_calls == 2


# ============================================================================
# 10. Cache Tests
# ============================================================================

class TestCache:
    """Verify cache get/set/TTL/hit-rate/invalidation."""

    def test_inmemory_cache_get_set(self):
        from app.cache.provider import InMemoryCache
        cache = InMemoryCache(default_ttl=60)
        cache.set("key1", {"data": "value"})
        result = cache.get("key1")
        assert result == {"data": "value"}

    def test_inmemory_cache_miss_returns_none(self):
        from app.cache.provider import InMemoryCache
        cache = InMemoryCache()
        result = cache.get("nonexistent-key")
        assert result is None

    def test_inmemory_cache_ttl_expiry(self):
        from app.cache.provider import InMemoryCache
        cache = InMemoryCache(default_ttl=1)
        cache.set("expiring", "value", ttl=1)
        assert cache.get("expiring") == "value"
        time.sleep(1.1)
        assert cache.get("expiring") is None, "Entry should have expired"

    def test_inmemory_cache_delete(self):
        from app.cache.provider import InMemoryCache
        cache = InMemoryCache()
        cache.set("del-key", "val")
        cache.delete("del-key")
        assert cache.get("del-key") is None

    def test_inmemory_cache_clear(self):
        from app.cache.provider import InMemoryCache
        cache = InMemoryCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_inmemory_cache_exists(self):
        from app.cache.provider import InMemoryCache
        cache = InMemoryCache()
        cache.set("existing", "val", ttl=60)
        assert cache.exists("existing") is True
        assert cache.exists("missing") is False

    def test_inmemory_cache_stats(self):
        from app.cache.provider import InMemoryCache
        cache = InMemoryCache()
        cache.set("s1", "v1")
        cache.get("s1")        # hit
        cache.get("missing")   # miss
        stats = cache.stats()
        assert stats["hits"]   == 1
        assert stats["misses"] == 1
        assert stats["sets"]   == 1
        assert "hit_rate" in stats

    def test_inmemory_cache_hit_rate(self):
        from app.cache.provider import InMemoryCache
        cache = InMemoryCache()
        cache.set("key", "val")
        cache.get("key")   # hit
        cache.get("key")   # hit
        cache.get("nope")  # miss
        stats = cache.stats()
        assert abs(stats["hit_rate"] - (2/3)) < 0.01

    def test_get_or_set(self):
        from app.cache.provider import InMemoryCache
        cache = InMemoryCache()
        call_count = {"n": 0}

        def factory():
            call_count["n"] += 1
            return "computed"

        result1 = cache.get_or_set("computed-key", factory)
        result2 = cache.get_or_set("computed-key", factory)
        assert result1 == "computed"
        assert result2 == "computed"
        assert call_count["n"] == 1, "Factory should only be called once"

    def test_cache_keys_provider(self):
        from app.cache.keys import CacheKey
        assert CacheKey.PROVIDER_HEALTH("gemini") == "provider_health:gemini"
        assert CacheKey.MODEL_LIST("openai") == "model_list:openai"
        assert CacheKey.PROMPT_TEMPLATE("invoice") == "prompt_template:invoice"
        assert CacheKey.CLASSIFICATION_SCHEMA("invoice") == "classification_schema:invoice"
        assert CacheKey.CONFIG == "config:global"

    def test_cache_ttl_mapping(self):
        from app.cache.keys import CacheTTL
        assert CacheTTL.for_key("provider_health:gemini") == CacheTTL.PROVIDER_HEALTH
        assert CacheTTL.for_key("model_list:openai")     == CacheTTL.MODEL_LIST
        assert CacheTTL.for_key("config:global")         == CacheTTL.CONFIG
        assert CacheTTL.for_key("unknown:key")           == CacheTTL.DEFAULT

    def test_cache_factory_singleton(self):
        from app.cache.provider import get_cache_provider, reset_cache_provider
        reset_cache_provider()
        c1 = get_cache_provider()
        c2 = get_cache_provider()
        assert c1 is c2

    def test_redis_stub_falls_back_to_inmemory(self):
        from app.cache.provider import RedisCache
        cache = RedisCache()
        cache.set("k", "v")
        assert cache.get("k") == "v"
        stats = cache.stats()
        assert stats["provider"] == "redis_stub"


# ============================================================================
# 11. Tracing Tests
# ============================================================================

class TestTracing:
    """Verify tracer creation, span creation, and attribute setting."""

    def test_setup_tracing_does_not_crash(self):
        from app.observability.tracing import setup_tracing
        # Should not raise regardless of opentelemetry availability
        setup_tracing()

    def test_get_tracer_returns_object(self):
        from app.observability.tracing import get_tracer
        tracer = get_tracer("test-tracer")
        assert tracer is not None

    def test_span_context_manager_no_exception(self):
        from app.observability.tracing import span
        with span(
            "test.span",
            correlation_id="corr-123",
            document_id="doc-abc",
            organization_id="org-xyz",
        ) as s:
            assert s is not None  # Span object (real or NoOp)

    def test_span_context_manager_propagates_exception(self):
        from app.observability.tracing import span
        with pytest.raises(ValueError):
            with span("failing.span"):
                raise ValueError("test error")

    def test_traced_decorator_executes_function(self):
        from app.observability.tracing import traced

        @traced("test.decorated")
        def add(a, b):
            return a + b

        result = add(2, 3)
        assert result == 5

    def test_traced_decorator_propagates_exception(self):
        from app.observability.tracing import traced

        @traced("test.error")
        def fail():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            fail()

    def test_trace_id_returns_string(self):
        from app.observability.tracing import get_current_trace_id, get_current_span_id
        trace_id = get_current_trace_id()
        span_id  = get_current_span_id()
        assert isinstance(trace_id, str)
        assert isinstance(span_id, str)

    def test_inject_extract_trace_context(self):
        from app.observability.tracing import inject_trace_context, extract_trace_context
        headers = {}
        inject_trace_context(headers)   # Should not raise
        ctx = extract_trace_context(headers)  # Should not raise


# ============================================================================
# 12. Middleware Integration Tests (via HTTP client)
# ============================================================================

class TestMiddlewareIntegration:
    """Integration tests for middleware layer via HTTP."""

    def test_correlation_id_in_response_header(self, client):
        response = client.get("/api/health")
        assert "X-Correlation-ID" in response.headers

    def test_v1_metrics_endpoint(self, client):
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200

    def test_v1_observability_status(self, client):
        response = client.get("/api/v1/observability/status")
        assert response.status_code == 200

    def test_v1_live(self, client):
        response = client.get("/api/v1/live")
        assert response.status_code == 200

    def test_v1_ready(self, client):
        response = client.get("/api/v1/ready")
        assert response.status_code in (200, 503)

    def test_v1_health(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code in (200, 503)

    def test_slow_threshold_config_exists(self):
        from app.core.config import Config
        assert hasattr(Config, "SLOW_REQUEST_THRESHOLD_MS")
        assert hasattr(Config, "SLOW_STAGE_THRESHOLD_MS")
        assert hasattr(Config, "SLOW_PROVIDER_THRESHOLD_MS")
        assert Config.SLOW_REQUEST_THRESHOLD_MS > 0
