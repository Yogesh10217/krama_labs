import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.db.models.organization import Organization
from app.repositories.organization import OrganizationRepository
from app.schemas.organization import OrganizationCreate
from app.core.exceptions import NotFoundException, KramaException, ConflictException
from fastapi import status

class OrganizationService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = OrganizationRepository(session)

    def create_organization(self, org_in: OrganizationCreate) -> Organization:
        if self.repo.slug_exists(org_in.slug):
            raise ConflictException(f"Organization with slug '{org_in.slug}' already exists.", "DUPLICATE_SLUG")
        
        org = Organization(name=org_in.name, slug=org_in.slug)
        self.repo.create(org)
        self.session.commit()
        return org

    def get_organization(self, org_id: uuid.UUID) -> Organization:
        org = self.repo.get_by_id(org_id)
        if not org:
            raise NotFoundException(f"Organization not found", "ORGANIZATION_NOT_FOUND")
        return org
