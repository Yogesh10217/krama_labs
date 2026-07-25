from datetime import date
from fastapi.testclient import TestClient
from app.security.dependencies import get_current_principal
from app.main import create_app

def override_get_current_principal():
    class DummyPrincipal:
        user_id = "test_user"
        organization_id = "test_org"
        roles = ["SYSTEM_ADMIN"]
    return DummyPrincipal()

def test_get_system_analytics(client: TestClient, app_instance):
    app_instance.dependency_overrides[get_current_principal] = override_get_current_principal
    try:
        response = client.get("/api/v1/admin/analytics/system")
        assert response.status_code == 200
        data = response.json()
        assert "daily_statistics" in data
        assert "sla_statistics" in data
    finally:
        app_instance.dependency_overrides.pop(get_current_principal, None)

def test_get_provider_analytics(client: TestClient, app_instance):
    app_instance.dependency_overrides[get_current_principal] = override_get_current_principal
    try:
        response = client.get("/api/v1/admin/analytics/providers")
        assert response.status_code == 200
        data = response.json()
        assert "provider_statistics" in data
        assert "cost_statistics" in data
    finally:
        app_instance.dependency_overrides.pop(get_current_principal, None)

def test_export_system_analytics(client: TestClient, app_instance):
    app_instance.dependency_overrides[get_current_principal] = override_get_current_principal
    try:
        response = client.get("/api/v1/admin/analytics/export?report_type=system&format=excel")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    finally:
        app_instance.dependency_overrides.pop(get_current_principal, None)


