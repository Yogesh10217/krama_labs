import uuid
from fastapi import status

def test_register_document(client, test_org):
    headers = {"X-Organization-ID": str(test_org.id)}
    claim_res = client.post("/api/v1/claims", json={"title": "Claim for Doc"}, headers=headers)
    claim_id = claim_res.json()["id"]
    
    doc_payload = {"original_filename": "test.pdf", "content_type": "application/pdf"}
    response = client.post(f"/api/v1/claims/{claim_id}/documents", json=doc_payload, headers=headers)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["original_filename"] == "test.pdf"
    assert data["claim_id"] == claim_id
    assert data["organization_id"] == str(test_org.id)

def test_get_document_cross_tenant_denied(client, db_session, test_org):
    headers = {"X-Organization-ID": str(test_org.id)}
    claim_res = client.post("/api/v1/claims", json={"title": "Claim for Doc"}, headers=headers)
    claim_id = claim_res.json()["id"]
    
    doc_res = client.post(f"/api/v1/claims/{claim_id}/documents", json={"original_filename": "test.pdf"}, headers=headers)
    doc_id = doc_res.json()["id"]

    from app.db.models.organization import Organization
    other_org = Organization(name="Other Org", slug=f"other-org-{uuid.uuid4().hex[:8]}")
    db_session.add(other_org)
    db_session.commit()
    db_session.refresh(other_org)

    other_headers = {"X-Organization-ID": str(other_org.id)}
    response = client.get(f"/api/v1/documents/{doc_id}", headers=other_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
