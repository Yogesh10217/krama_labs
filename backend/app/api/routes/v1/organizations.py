import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.organization import OrganizationCreate, OrganizationResponse
from app.services.organization_service import OrganizationService

router = APIRouter()

@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(org_in: OrganizationCreate, db: Session = Depends(get_db)):
    """Bootstrap a new organization."""
    service = OrganizationService(db)
    return service.create_organization(org_in)

@router.get("/{organization_id}", response_model=OrganizationResponse)
def get_organization(organization_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get an organization by ID."""
    service = OrganizationService(db)
    return service.get_organization(organization_id)
