import pytest
from unittest.mock import patch
from fastapi import status
from sqlalchemy import select
from app.db.models.claim import Claim

def test_rollback_on_failure(client, db_session, test_org):
    """
    Test that if a service throws an exception, the transaction is rolled back.
    We will mock the service commit to raise an exception.
    """
    headers = {"X-Organization-ID": str(test_org.id)}
    payload = {"title": "Rollback Test Claim"}

    # Mock the flush/commit so that the database throws or we manually raise an exception
    with patch("app.services.claim_service.ClaimService.create_claim") as mock_create:
        mock_create.side_effect = Exception("Simulated DB failure")
        
        # FastAPI will catch the generic exception and return a 500, and the dependency will rollback.
        # However, our custom KramaException handler in main.py catches KramaException. 
        # A generic Exception will be caught by generic handlers or just bubble up (causing 500).
        response = client.post("/api/v1/claims", json=payload, headers=headers)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    # Verify that the claim was NOT created (rolled back)
    claims = db_session.execute(select(Claim).where(Claim.title == "Rollback Test Claim")).scalars().all()
    assert len(claims) == 0
