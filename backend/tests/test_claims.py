import uuid
from fastapi import status

def test_create_claim(client, test_org):
    headers = {"X-Organization-ID": str(test_org.id)}
    payload = {"title": "Test Claim", "external_reference": "REF-123"}
    
    response = client.post("/api/v1/claims", json=payload, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Test Claim"
    assert data["external_reference"] == "REF-123"
    assert data["organization_id"] == str(test_org.id)
    assert data["status"] == "DRAFT"

def test_create_claim_duplicate_ext_ref(client, test_org):
    headers = {"X-Organization-ID": str(test_org.id)}
    payload = {"title": "Test Claim 2", "external_reference": "REF-DUP"}
    
    client.post("/api/v1/claims", json=payload, headers=headers)
    response = client.post("/api/v1/claims", json=payload, headers=headers)
    
    assert response.status_code == status.HTTP_409_CONFLICT

def test_get_claim_cross_tenant_denied(client, db_session, test_org):
    # Create claim in test_org
    headers = {"X-Organization-ID": str(test_org.id)}
    payload = {"title": "Tenant A Claim"}
    response = client.post("/api/v1/claims", json=payload, headers=headers)
    claim_id = response.json()["id"]

    # Try to access with a different org header
    from app.db.models.organization import Organization
    other_org = Organization(name="Other Org", slug=f"other-org-{uuid.uuid4().hex[:8]}")
    db_session.add(other_org)
    db_session.commit()
    db_session.refresh(other_org)

    other_headers = {"X-Organization-ID": str(other_org.id)}
    response2 = client.get(f"/api/v1/claims/{claim_id}", headers=other_headers)
    
    # Must be 404 to prevent leakage
    assert response2.status_code == status.HTTP_404_NOT_FOUND

def test_missing_org_header(client):
    response = client.post("/api/v1/claims", json={"title": "No Org"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"]["code"] == "ORGANIZATION_CONTEXT_REQUIRED"
