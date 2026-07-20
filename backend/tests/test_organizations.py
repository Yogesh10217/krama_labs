from fastapi import status

def test_create_organization(client):
    response = client.post("/api/v1/organizations", json={"name": "Org 1", "slug": "org-1"})
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Org 1"
    assert data["slug"] == "org-1"
    assert "id" in data

def test_create_duplicate_organization_slug(client):
    client.post("/api/v1/organizations", json={"name": "Org 2", "slug": "org-duplicate"})
    response = client.post("/api/v1/organizations", json={"name": "Org 3", "slug": "org-duplicate"})
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["error"]["code"] == "DUPLICATE_SLUG"

def test_get_organization(client):
    create_response = client.post("/api/v1/organizations", json={"name": "Org 4", "slug": "org-4"})
    org_id = create_response.json()["id"]

    get_response = client.get(f"/api/v1/organizations/{org_id}")
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["id"] == org_id
