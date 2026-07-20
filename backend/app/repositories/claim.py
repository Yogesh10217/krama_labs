import uuid
from typing import Optional, List, Tuple
from sqlalchemy import select, func, exists, and_
from sqlalchemy.orm import Session
from app.db.models.claim import Claim

class ClaimRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id_and_org(self, claim_id: uuid.UUID, organization_id: uuid.UUID) -> Optional[Claim]:
        """Tenant-isolated claim retrieval."""
        stmt = select(Claim).where(and_(Claim.id == claim_id, Claim.organization_id == organization_id))
        return self.session.execute(stmt).scalar_one_or_none()

    def create(self, claim: Claim) -> Claim:
        self.session.add(claim)
        self.session.flush()
        return claim

    def list_by_org(self, organization_id: uuid.UUID, skip: int = 0, limit: int = 20) -> Tuple[List[Claim], int]:
        """Returns paginated claims and total count for an organization."""
        stmt = select(Claim).where(Claim.organization_id == organization_id).order_by(Claim.created_at.desc())
        items = list(self.session.execute(stmt.offset(skip).limit(limit)).scalars().all())
        
        count_stmt = select(func.count()).select_from(Claim).where(Claim.organization_id == organization_id)
        total = self.session.execute(count_stmt).scalar_one()
        
        return items, total

    def external_reference_exists(self, organization_id: uuid.UUID, external_reference: str) -> bool:
        if external_reference is None:
            return False
        stmt = select(exists().where(and_(Claim.organization_id == organization_id, Claim.external_reference == external_reference)))
        return self.session.execute(stmt).scalar()
