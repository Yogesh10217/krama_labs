import uuid
from typing import Optional, List, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from app.db.models.job import Job

class JobRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id_and_org(self, job_id: uuid.UUID, organization_id: uuid.UUID) -> Optional[Job]:
        """Tenant-isolated job retrieval."""
        stmt = select(Job).where(and_(Job.id == job_id, Job.organization_id == organization_id))
        return self.session.execute(stmt).scalar_one_or_none()

    def create(self, job: Job) -> Job:
        self.session.add(job)
        self.session.flush()
        return job

    def list_by_claim_and_org(self, claim_id: uuid.UUID, organization_id: uuid.UUID, skip: int = 0, limit: int = 20) -> Tuple[List[Job], int]:
        """Returns paginated jobs and total count for a claim."""
        stmt = select(Job).where(and_(Job.claim_id == claim_id, Job.organization_id == organization_id)).order_by(Job.created_at.desc())
        items = list(self.session.execute(stmt.offset(skip).limit(limit)).scalars().all())
        
        count_stmt = select(func.count()).select_from(Job).where(and_(Job.claim_id == claim_id, Job.organization_id == organization_id))
        total = self.session.execute(count_stmt).scalar_one()
        
        return items, total
