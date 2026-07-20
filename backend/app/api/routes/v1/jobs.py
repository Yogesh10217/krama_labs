import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.organization import Organization
from app.api.dependencies import get_organization_context
from app.schemas.job import JobCreate, JobResponse, JobListResponse
from app.schemas.common import PaginationMetadata
from app.services.job_service import JobService
import math

router = APIRouter()

@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job_in: JobCreate,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    service = JobService(db)
    return service.create_job(org.id, job_in)

@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(
    job_id: uuid.UUID,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    service = JobService(db)
    return service.get_job(job_id, org.id)

@router.get("/claims/{claim_id}/jobs", response_model=JobListResponse)
def list_claim_jobs(
    claim_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    service = JobService(db)
    skip = (page - 1) * page_size
    items, total_items = service.list_claim_jobs(claim_id, org.id, skip=skip, limit=page_size)
    
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
    pagination = PaginationMetadata(page=page, page_size=page_size, total_items=total_items, total_pages=total_pages)
    
    return JobListResponse(items=items, pagination=pagination)
