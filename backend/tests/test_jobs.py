from fastapi import status

def test_create_job(client, test_org):
    headers = {"X-Organization-ID": str(test_org.id)}
    claim_res = client.post("/api/v1/claims", json={"title": "Claim for Job"}, headers=headers)
    claim_id = claim_res.json()["id"]

    job_payload = {"claim_id": claim_id, "job_type": "DOCUMENT_PROCESSING"}
    response = client.post("/api/v1/jobs", json=job_payload, headers=headers)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["claim_id"] == claim_id
    assert data["job_type"] == "DOCUMENT_PROCESSING"
    assert data["status"] == "PENDING"
    assert data["progress"] == 0

def test_create_job_invalid_claim_association(client, test_org):
    headers = {"X-Organization-ID": str(test_org.id)}
    # Missing both claim_id and document_id
    job_payload = {"job_type": "DOCUMENT_PROCESSING"}
    response = client.post("/api/v1/jobs", json=job_payload, headers=headers)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"]["code"] == "INVALID_JOB_ASSOCIATION"
