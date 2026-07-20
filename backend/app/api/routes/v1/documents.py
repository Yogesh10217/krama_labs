import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.organization import Organization
from app.api.dependencies import get_organization_context
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentListResponse
from app.schemas.common import PaginationMetadata
from app.services.document_service import DocumentService
import math

router = APIRouter()

# Note: In FastAPI, it's easier to mount this router and handle the paths explicitly
# We'll prefix this router with /claims in the main router, or handle it as is.
# We will define it as /claims/{claim_id}/documents and /documents/{document_id}

@router.post("/claims/{claim_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def register_document(
    claim_id: uuid.UUID,
    doc_in: DocumentCreate,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    service = DocumentService(db)
    return service.register_document(org.id, claim_id, doc_in)

@router.get("/claims/{claim_id}/documents", response_model=DocumentListResponse)
def list_claim_documents(
    claim_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    service = DocumentService(db)
    skip = (page - 1) * page_size
    items, total_items = service.list_claim_documents(claim_id, org.id, skip=skip, limit=page_size)
    
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
    pagination = PaginationMetadata(page=page, page_size=page_size, total_items=total_items, total_pages=total_pages)
    
    return DocumentListResponse(items=items, pagination=pagination)

@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: uuid.UUID,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    service = DocumentService(db)
    return service.get_document(document_id, org.id)
