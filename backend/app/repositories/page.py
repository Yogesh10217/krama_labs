import uuid
from typing import Optional, List
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import Session
from app.db.models.page import Page
from app.db.models.document import Document


class PageRepository:
    """Repository managing Page model database transactions."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, page: Page) -> Page:
        self.session.add(page)
        self.session.flush()
        return page

    def get_by_id_and_org(self, page_id: uuid.UUID, organization_id: uuid.UUID) -> Optional[Page]:
        """Tenant-isolated page retrieval, ensuring the page belongs to the tenant's document."""
        stmt = select(Page).join(Document).where(
            and_(
                Page.id == page_id,
                Document.organization_id == organization_id,
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by_document_and_org(self, document_id: uuid.UUID, organization_id: uuid.UUID) -> List[Page]:
        """Tenant-isolated page retrieval for a document, ordered deterministically by page_number."""
        stmt = select(Page).join(Document).where(
            and_(
                Page.document_id == document_id,
                Document.organization_id == organization_id,
            )
        ).order_by(Page.page_number.asc())
        return list(self.session.execute(stmt).scalars().all())

    def delete_by_document(self, document_id: uuid.UUID) -> None:
        """Delete all pages associated with the document_id."""
        stmt = delete(Page).where(Page.document_id == document_id)
        self.session.execute(stmt)
        self.session.flush()
