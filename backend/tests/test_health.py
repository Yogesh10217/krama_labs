"""Tests for health, readiness, and liveness endpoints."""

import pytest
from fastapi import status


def test_liveness_endpoint(client):
    """Test GET /api/live returns HTTP 200 and status ok."""
    response = client.get("/api/live")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
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
    """Test GET /api/health returns HTTP 200 and metadata description."""
    response = client.get("/api/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data
    assert "features" in data
    
    # Verify no credentials or internal URLs are leaked
    for key in ["key", "token", "password", "secret", "url", "db", "redis"]:
        for data_key, val in data.items():
            assert key not in str(data_key).lower()
            if isinstance(val, dict):
                for sub_key in val.keys():
                    assert key not in str(sub_key).lower()


def test_v1_health_endpoints(client):
    """Test versioned v1 health paths work identically."""
    for path in ["/api/v1/live", "/api/v1/ready", "/api/v1/health"]:
        response = client.get(path)
        assert response.status_code == status.HTTP_200_OK
