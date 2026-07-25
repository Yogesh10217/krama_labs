import uuid
from typing import Annotated
from fastapi import Header, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.exceptions import KramaException, NotFoundException
from app.db.models.organization import Organization
from app.services.organization_service import OrganizationService
from app.security.dependencies import get_current_principal, Principal

class OrganizationContextRequiredException(KramaException):
    def __init__(self):
        super().__init__("X-Organization-ID header is required for this endpoint.", "ORGANIZATION_CONTEXT_REQUIRED", status.HTTP_400_BAD_REQUEST)

class InvalidOrganizationContextException(KramaException):
    def __init__(self):
        super().__init__("Invalid X-Organization-ID format.", "INVALID_ORGANIZATION_CONTEXT", status.HTTP_400_BAD_REQUEST)


def get_organization_context(
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Organization:
    """
    Dependency to enforce organization context for APIs.
    Uses the authenticated Principal to resolve the organization.
    """
    if not principal.organization_id:
        raise OrganizationContextRequiredException()

    org_id = principal.organization_id

    service = OrganizationService(db)
    try:
        org = service.get_organization(org_id)
        return org
    except NotFoundException:
        raise KramaException("Organization context not found or access denied.", "ORGANIZATION_ACCESS_DENIED", status.HTTP_403_FORBIDDEN)
