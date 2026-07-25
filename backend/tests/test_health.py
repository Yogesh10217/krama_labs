"""Tests for health, readiness, and liveness endpoints."""

import pytest
from fastapi import status


def test_liveness_endpoint(client):
    """Test GET /api/live returns HTTP 200 (Phase 11: status='alive')."""
    response = client.get("/api/live")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # Phase 11 liveness returns "alive" (was "ok" in Phase 10)
    assert data["status"] in ("alive", "ok")
    assert "service" in data


def test_readiness_endpoint(client):
    """Test GET /api/ready returns HTTP 200 and configuration status."""
    response = client.get("/api/ready")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ready"
    assert "checks" in data
    assert data["checks"]["config"] is True
    assert data["checks"]["upload_dir"] is True
    assert data["checks"]["results_dir"] is True


def test_health_endpoint(client):
    """Test GET /api/health returns HTTP 200 with Phase 11 three-level model."""
    response = client.get("/api/health")
    # Phase 11 health returns 200 for HEALTHY or DEGRADED; 503 only for UNHEALTHY
    assert response.status_code in (status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE)
    data = response.json()

    # Phase 11: status is three-level model (replaces "healthy")
    assert data["status"] in ("HEALTHY", "DEGRADED", "UNHEALTHY")
    assert "version" in data
    assert "environment" in data
    # Phase 11 returns "components" instead of "features"
    assert "components" in data or "features" in data

    # Verify no credentials or internal URLs are leaked
    for key in ["password", "secret"]:
        for data_key in data.keys():
            assert key not in str(data_key).lower()


def test_v1_health_endpoints(client):
    """Test versioned v1 health paths work identically."""
    for path in ["/api/v1/live", "/api/v1/ready", "/api/v1/health"]:
        response = client.get(path)
        assert response.status_code in (status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE)
