import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.organization import Organization
from app.api.dependencies import get_organization_context
from app.schemas.claim import ClaimCreate, ClaimUpdate, ClaimResponse, ClaimListResponse
from app.schemas.common import PaginationMetadata
from app.services.claim_service import ClaimService
import math

router = APIRouter()

@router.post("", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
def create_claim(
    claim_in: ClaimCreate,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    service = ClaimService(db)
    return service.create_claim(org.id, claim_in)

@router.get("", response_model=ClaimListResponse)
def list_claims(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    service = ClaimService(db)
    skip = (page - 1) * page_size
    items, total_items = service.list_claims(org.id, skip=skip, limit=page_size)
    
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
    pagination = PaginationMetadata(page=page, page_size=page_size, total_items=total_items, total_pages=total_pages)
    
    return ClaimListResponse(items=items, pagination=pagination)

@router.get("/{claim_id}", response_model=ClaimResponse)
def get_claim(
    claim_id: uuid.UUID,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    service = ClaimService(db)
    return service.get_claim(claim_id, org.id)

@router.patch("/{claim_id}", response_model=ClaimResponse)
def update_claim(
    claim_id: uuid.UUID,
    claim_update: ClaimUpdate,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    service = ClaimService(db)
    return service.update_claim(claim_id, org.id, claim_update)
