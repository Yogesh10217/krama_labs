import uuid
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.db.models.job import Job
from app.repositories.job import JobRepository
from app.schemas.job import JobCreate
from app.core.exceptions import NotFoundException, ValidationException
from app.services.claim_service import ClaimService
from app.services.document_service import DocumentService

class JobService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = JobRepository(session)
        self.claim_service = ClaimService(session)
        self.document_service = DocumentService(session)

    def create_job(self, organization_id: uuid.UUID, job_in: JobCreate) -> Job:
        if not job_in.claim_id and not job_in.document_id:
            raise ValidationException("Job must be associated with at least a claim or a document.", "INVALID_JOB_ASSOCIATION")

        if job_in.claim_id:
            # Validate ownership
            self.claim_service.get_claim(job_in.claim_id, organization_id)
            
        if job_in.document_id:
            # Validate ownership
            self.document_service.get_document(job_in.document_id, organization_id)

        job = Job(
            organization_id=organization_id,
            claim_id=job_in.claim_id,
            document_id=job_in.document_id,
            job_type=job_in.job_type
        )
        self.repo.create(job)
        self.session.commit()
        return job

    def get_job(self, job_id: uuid.UUID, organization_id: uuid.UUID) -> Job:
        job = self.repo.get_by_id_and_org(job_id, organization_id)
        if not job:
            raise NotFoundException("Job not found", "JOB_NOT_FOUND")
        return job

    def list_claim_jobs(self, claim_id: uuid.UUID, organization_id: uuid.UUID, skip: int = 0, limit: int = 20) -> Tuple[List[Job], int]:
        # Validate claim ownership
        self.claim_service.get_claim(claim_id, organization_id)
        return self.repo.list_by_claim_and_org(claim_id, organization_id, skip, limit)
