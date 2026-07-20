import uuid
from typing import Optional
from sqlalchemy import select, exists
from sqlalchemy.orm import Session
from app.db.models.organization import Organization

class OrganizationRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, organization_id: uuid.UUID) -> Optional[Organization]:
        return self.session.execute(select(Organization).where(Organization.id == organization_id)).scalar_one_or_none()

    def get_by_slug(self, slug: str) -> Optional[Organization]:
        return self.session.execute(select(Organization).where(Organization.slug == slug)).scalar_one_or_none()

    def slug_exists(self, slug: str) -> bool:
        return self.session.execute(select(exists().where(Organization.slug == slug))).scalar()

    def create(self, organization: Organization) -> Organization:
        self.session.add(organization)
        self.session.flush()
        return organization
