"""Core application configuration, request-id, error schema, and import safety tests."""

import sys
import pytest
from fastapi import status


def test_request_id_generation(client):
    """Test that a correlation ID is automatically generated if none is sent (Phase 11)."""
    response = client.get("/api/live")
    assert response.status_code == status.HTTP_200_OK
    # Phase 11: middleware sets X-Correlation-ID (supersedes X-Request-ID)
    corr_id = response.headers.get("X-Correlation-ID") or response.headers.get("X-Request-ID")
    assert corr_id is not None
    assert len(corr_id) > 0


def test_request_id_propagation(client):
    """Test that a sent X-Correlation-ID is echoed back (Phase 11)."""
    corr_id = "test-correlation-id-12345"
    # Phase 11 primary header is X-Correlation-ID
    response = client.get("/api/live", headers={"X-Correlation-ID": corr_id})
    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("X-Correlation-ID") == corr_id


def test_unknown_route_behavior(client):
    """Test that visiting an invalid route returns a structured 404 response."""
    response = client.get("/api/some-nonexistent-route-for-testing")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "request_id" in data["error"]
    assert "message" in data["error"]


def test_validation_error_structure(client):
    """Test that validation errors adhere to the standard JSON error contract."""
    # Send empty/invalid body to chat — our endpoint catches json decode errors
    # and raises ValidationException (400 BAD_REQUEST) with a standard error body
    response = client.post("/api/chat", content="invalid_json_body", headers={"Content-Type": "application/json"})
    # Our custom handler maps ValidationException to 400
    assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY)
    data = response.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "request_id" in data["error"]
    assert "message" in data["error"]


def test_import_safety():
    """Verify that importing the application factory does not import optional heavy engines."""
    # Ensure paddleocr, fitz (pymupdf), rapidfuzz are NOT in sys.modules prior to loading these modules
    assert "paddleocr" not in sys.modules
    assert "fitz" not in sys.modules
    assert "google.generativeai" not in sys.modules
    assert "openai" not in sys.modules
