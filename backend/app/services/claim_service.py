import uuid
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.db.models.claim import Claim
from app.repositories.claim import ClaimRepository
from app.schemas.claim import ClaimCreate, ClaimUpdate
from app.core.exceptions import NotFoundException, KramaException, ConflictException
from app.domain.lifecycle import validate_claim_transition

class ClaimService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = ClaimRepository(session)

    def create_claim(self, organization_id: uuid.UUID, claim_in: ClaimCreate) -> Claim:
        if self.repo.external_reference_exists(organization_id, claim_in.external_reference):
            raise ConflictException("Claim with this external reference already exists in the organization.", "DUPLICATE_EXTERNAL_REFERENCE")
        
        claim = Claim(
            organization_id=organization_id,
            external_reference=claim_in.external_reference,
            claim_type=claim_in.claim_type,
            priority=claim_in.priority,
            title=claim_in.title,
            description=claim_in.description
        )
        self.repo.create(claim)
        self.session.commit()
        return claim

    def get_claim(self, claim_id: uuid.UUID, organization_id: uuid.UUID) -> Claim:
        claim = self.repo.get_by_id_and_org(claim_id, organization_id)
        if not claim:
            # Mask existence cross-tenant
            raise NotFoundException("Claim not found", "CLAIM_NOT_FOUND")
        return claim

    def list_claims(self, organization_id: uuid.UUID, skip: int = 0, limit: int = 20) -> Tuple[List[Claim], int]:
        return self.repo.list_by_org(organization_id, skip, limit)

    def update_claim(self, claim_id: uuid.UUID, organization_id: uuid.UUID, claim_update: ClaimUpdate) -> Claim:
        claim = self.get_claim(claim_id, organization_id)
        
        if claim_update.status and claim_update.status != claim.status:
            validate_claim_transition(claim.status, claim_update.status)
            claim.status = claim_update.status
            
        if claim_update.priority is not None:
            claim.priority = claim_update.priority
        if claim_update.title is not None:
            claim.title = claim_update.title
        if claim_update.description is not None:
            claim.description = claim_update.description
            
        self.session.flush()
        self.session.commit()
        return claim
