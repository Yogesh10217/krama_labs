import uuid
from typing import Optional, List, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from app.db.models.document import Document
from app.domain.enums import DocumentStatus


class DocumentRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id_and_org(self, document_id: uuid.UUID, organization_id: uuid.UUID) -> Optional[Document]:
        """Tenant-isolated document retrieval."""
        stmt = select(Document).where(and_(Document.id == document_id, Document.organization_id == organization_id))
        return self.session.execute(stmt).scalar_one_or_none()

    def create(self, document: Document) -> Document:
        self.session.add(document)
        self.session.flush()
        return document

    def list_by_claim_and_org(self, claim_id: uuid.UUID, organization_id: uuid.UUID, skip: int = 0, limit: int = 20) -> Tuple[List[Document], int]:
        """Returns paginated documents and total count for a claim."""
        stmt = select(Document).where(and_(Document.claim_id == claim_id, Document.organization_id == organization_id)).order_by(Document.created_at.desc())
        items = list(self.session.execute(stmt.offset(skip).limit(limit)).scalars().all())

        count_stmt = select(func.count()).select_from(Document).where(and_(Document.claim_id == claim_id, Document.organization_id == organization_id))
        total = self.session.execute(count_stmt).scalar_one()

        return items, total

    def find_active_by_checksum_in_claim(
        self,
        claim_id: uuid.UUID,
        checksum: str,
    ) -> Optional[Document]:
        """Find a non-archived document with the given checksum inside a specific claim.

        Used for duplicate detection (same bytes + same claim → reject).
        Does NOT query across organizations, ensuring no cross-tenant leakage.

        Phase 2 duplicate policy:
            - Same checksum + same claim → DUPLICATE_DOCUMENT (409).
            - Same checksum + different claim → allowed.
            - Same checksum + different organization → allowed, no leakage.
        """
        stmt = select(Document).where(
            and_(
                Document.claim_id == claim_id,
                Document.checksum == checksum,
                Document.status != DocumentStatus.ARCHIVED,
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()
