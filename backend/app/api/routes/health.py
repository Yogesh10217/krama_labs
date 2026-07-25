"""
app/api/routes/health.py — Phase 11 Enhanced Health Endpoints

Strict endpoint responsibilities (per approved spec):

  GET /live   → Liveness probe
    - No I/O
    - Returns 200 always (proves process is running)
    - Kubernetes: liveness probe target

  GET /ready  → Readiness probe
    - Fast filesystem + config checks only (< 100ms)
    - Returns 200 (ready) or 503 (not ready)
    - Kubernetes: readiness probe target

  GET /health → Full diagnostic health
    - Database, storage, queue, AI providers, config
    - Returns 200 (HEALTHY/DEGRADED) or 503 (UNHEALTHY)
    - Three-level model: HEALTHY | DEGRADED | UNHEALTHY
    - May be slower (up to 2s); not intended for frequent polling

These endpoints intentionally do NOT import or depend on any business service.
"""

import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.core.config import Config
from app.db.session import get_db
from app.observability.health import HealthChecker, HealthLevel
from app.observability.readiness import ReadinessChecker, ReadinessStatus, liveness_response

router = APIRouter()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# GET /live — Liveness probe
# ---------------------------------------------------------------------------

@router.get(
    "/live",
    tags=["Health"],
    summary="Liveness probe",
    description=(
        "Confirms that the process is alive. Performs no I/O. "
        "Always returns HTTP 200. "
        "Use as a Kubernetes liveness probe target."
    ),
)
async def live():
    """Ultra-lightweight liveness check. Never returns 503."""
    return liveness_response()


# ---------------------------------------------------------------------------
# GET /ready — Readiness probe
# ---------------------------------------------------------------------------

@router.get(
    "/ready",
    tags=["Health"],
    summary="Readiness probe",
    description=(
        "Checks whether the service is ready to accept traffic. "
        "Verifies config validity and required filesystem directories. "
        "Returns 200 when ready, 503 when not ready. "
        "Use as a Kubernetes readiness probe target."
    ),
)
async def ready():
    """Fast readiness check (< 100ms). Config + filesystem only."""
    checker = ReadinessChecker()
    report  = checker.check()

    if report.status == ReadinessStatus.READY:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=report.to_dict(),
        )
    else:
        logger.warning("Readiness check failed: %s", report.details)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=report.to_dict(),
        )


# ---------------------------------------------------------------------------
# GET /health — Full diagnostic health (three-level)
# ---------------------------------------------------------------------------

@router.get(
    "/health",
    tags=["Health"],
    summary="Full diagnostic health check",
    description=(
        "Runs all health probes: database, storage, queue, AI providers, config. "
        "Returns three-level status: HEALTHY | DEGRADED | UNHEALTHY. "
        "HTTP 200 for HEALTHY or DEGRADED (service is serving). "
        "HTTP 503 for UNHEALTHY (service cannot serve requests)."
    ),
)
async def health(db=Depends(get_db)):
    """
    Full health diagnostic. May take up to 2s.

    HEALTHY:   All components operational.
    DEGRADED:  Service is operational with reduced capacity or warnings.
    UNHEALTHY: Service cannot safely serve requests.
    """
    # Provide db factory so the database probe can open its own session
    from app.db.session import SessionLocal

    try:
        # Import the globally started queue if available
        from app.api.routes.v1.jobs_async import get_queue
        queue = get_queue()
    except Exception:
        queue = None

    checker = HealthChecker(
        db_factory=SessionLocal,
        queue=queue,
    )
    report = checker.check()

    http_status = (
        status.HTTP_200_OK
        if report.is_serving
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    if not report.is_serving:
        logger.error(
            "Health check returned UNHEALTHY: %s",
            [c.detail for c in report.components if c.level == HealthLevel.UNHEALTHY],
        )
    elif report.overall == HealthLevel.DEGRADED:
        logger.warning(
            "Health check returned DEGRADED: %s",
            [c.detail for c in report.components if c.level == HealthLevel.DEGRADED],
        )

    return JSONResponse(
        status_code=http_status,
        content=report.to_dict(),
    )
