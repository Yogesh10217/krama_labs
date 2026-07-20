import uuid
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.db.models.document import Document
from app.repositories.document import DocumentRepository
from app.schemas.document import DocumentCreate
from app.core.exceptions import NotFoundException
from app.services.claim_service import ClaimService

class DocumentService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = DocumentRepository(session)
        self.claim_service = ClaimService(session)

    def register_document(self, organization_id: uuid.UUID, claim_id: uuid.UUID, doc_in: DocumentCreate) -> Document:
        # Validate claim ownership (raises NotFoundException if not found or cross-tenant)
        self.claim_service.get_claim(claim_id, organization_id)
        
        doc = Document(
            organization_id=organization_id,
            claim_id=claim_id,
            original_filename=doc_in.original_filename,
            content_type=doc_in.content_type,
            file_extension=doc_in.file_extension,
            size_bytes=doc_in.size_bytes,
            document_type=doc_in.document_type
        )
        self.repo.create(doc)
        self.session.commit()
        return doc

    def get_document(self, document_id: uuid.UUID, organization_id: uuid.UUID) -> Document:
        doc = self.repo.get_by_id_and_org(document_id, organization_id)
        if not doc:
            raise NotFoundException("Document not found", "DOCUMENT_NOT_FOUND")
        return doc

    def list_claim_documents(self, claim_id: uuid.UUID, organization_id: uuid.UUID, skip: int = 0, limit: int = 20) -> Tuple[List[Document], int]:
        # Validate claim ownership
        self.claim_service.get_claim(claim_id, organization_id)
        return self.repo.list_by_claim_and_org(claim_id, organization_id, skip, limit)
