import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.domain.enums import DocumentStatus
from app.schemas.common import PaginatedResponse

class DocumentBase(BaseModel):
    original_filename: str
    content_type: Optional[str] = None
    file_extension: Optional[str] = None
    size_bytes: Optional[int] = None
    document_type: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    claim_id: uuid.UUID
    storage_key: Optional[str] = None
    checksum: Optional[str] = None
    status: DocumentStatus
    page_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

DocumentListResponse = PaginatedResponse[DocumentResponse]
